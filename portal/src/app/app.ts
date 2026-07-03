import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonComponent } from './components/ui/button.component';
import { InputComponent } from './components/ui/input.component';
import { SwitchComponent } from './components/ui/switch.component';
import { DatepickerComponent } from './components/ui/datepicker.component';
import { ModalComponent } from './components/ui/modal.component';
import { BankCardComponent } from './components/bank-card.component';
import { BankService, BankResponse } from './services/bank.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    FormsModule,
    ButtonComponent,
    InputComponent,
    SwitchComponent,
    DatepickerComponent,
    ModalComponent,
    BankCardComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  private readonly bankService = inject(BankService);

  // Signals for core state
  readonly banks = signal<BankResponse[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly statusMessage = signal<string>('');
  readonly searchQuery = signal<string>('');

  // Reusable controls demo state
  readonly excludeZeroBalances = signal<boolean>(false);
  readonly filterDateStart = signal<string>('');
  readonly filterDateEnd = signal<string>('');
  
  // Settings modal fields (Inputs)
  readonly showSettingsModal = signal<boolean>(false);
  readonly configDNI = signal<string>('');
  readonly configUser = signal<string>('');
  readonly configPassword = signal<string>('');

  // 2FA OTP Modal Signals
  readonly showOTPModal = signal<boolean>(false);
  readonly otpCode = signal<string>('');
  readonly pendingQuery = signal<'all' | string | null>(null);

  // Total sums computations
  readonly totals = computed(() => {
    let totalVES = 0;
    let totalUSD = 0;

    for (const bank of this.banks()) {
      if (!bank.data) continue;
      
      if (typeof bank.data === 'string') {
        const val = this.parseNumeric(bank.data);
        totalVES += val;
      } else if (Array.isArray(bank.data)) {
        for (const item of bank.data) {
          const val = this.parseNumeric(item.value);
          const valLower = item.value.toLowerCase();
          
          if (valLower.includes('usd') || valLower.includes('$')) {
            totalUSD += val;
          } else {
            totalVES += val;
          }
        }
      }
    }

    return {
      ves: totalVES.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      usd: totalUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    };
  });

  // Filtered banks calculation based on search and switch state
  readonly filteredBanks = computed(() => {
    let list = this.banks();
    
    // 1. Text filter
    const query = this.searchQuery().toLowerCase().trim();
    if (query) {
      list = list.filter(bank => 
        bank.label.toLowerCase().includes(query) || 
        bank.code.includes(query)
      );
    }

    // 2. Exclude Zero Balances switch filter
    if (this.excludeZeroBalances()) {
      list = list.map(bank => {
        if (!bank.data) return bank;
        if (typeof bank.data === 'string') {
          return this.parseNumeric(bank.data) > 0 ? bank : { ...bank, data: null };
        }
        if (Array.isArray(bank.data)) {
          const filteredData = bank.data.filter(item => this.parseNumeric(item.value) > 0);
          return { ...bank, data: filteredData };
        }
        return bank;
      });
    }

    return list;
  });

  ngOnInit() {
    this.loadInitialBanks();
  }

  private async loadInitialBanks() {
    try {
      this.statusMessage.set('Conectando con el servidor...');
      const data = await this.bankService.getBanks();
      const formatted: BankResponse[] = data.map((b: any) => ({
        label: b.label,
        code: b.code,
        config: b.config,
        data: null
      }));
      this.banks.set(formatted);
      this.statusMessage.set('');
    } catch (e) {
      console.warn('Could not connect to backend, loading default local banks.', e);
      this.fallbackBanks();
    }
  }

  private fallbackBanks() {
    this.banks.set([
      { 
        label: 'Bancamiga', 
        code: '0172', 
        config: [
          { label: 'Google Authenticator', key: 'google-auth', required: true }
        ],
        data: null 
      },
      { label: 'Banco Nacional de Crédito', code: '0191', data: null }
    ]);
    this.statusMessage.set('');
  }

  async runAllQueries(otp?: string) {
    if (this.isLoading()) return;
    
    // Check if any active bank in banks requires google-auth
    const needsOTP = this.banks().some(b => b.config?.some(c => c.key === 'google-auth'));
    if (needsOTP && !otp) {
      this.pendingQuery.set('all');
      this.showOTPModal.set(true);
      return;
    }

    this.isLoading.set(true);
    this.statusMessage.set('Sincronizando cuentas en paralelo. Por favor espera...');
    
    // Clear old errors
    this.banks.update(current => 
      current.map(b => ({ ...b, error: undefined }))
    );

    try {
      const data = await this.bankService.queryAll(otp);
      this.banks.set(data.map((b: any) => ({
        label: b.label,
        code: b.code,
        config: b.config || this.banks().find(x => x.code === b.code)?.config,
        data: b.data,
        error: b.error || undefined
      })));
      this.statusMessage.set('Cuentas actualizadas.');
    } catch (e: any) {
      this.statusMessage.set(`Error de conexión: ${e.message || e}`);
    } finally {
      this.isLoading.set(false);
    }
  }

  async runSingleQuery(code: string, otp?: string) {
    if (this.isLoading()) return;
    
    const bank = this.banks().find(b => b.code === code);
    const needsOTP = bank?.config?.some(c => c.key === 'google-auth');
    if (needsOTP && !otp) {
      this.pendingQuery.set(code);
      this.showOTPModal.set(true);
      return;
    }

    this.isLoading.set(true);
    const bankName = bank?.label || 'Banco';
    this.statusMessage.set(`Consultando ${bankName}...`);
    
    this.banks.update(current => 
      current.map(b => b.code === code ? { ...b, error: undefined } : b)
    );

    try {
      const data = await this.bankService.queryByBank(code, otp);
      this.banks.update(current => 
        current.map(b => b.code === code ? { ...b, data } : b)
      );
      this.statusMessage.set('Actualizado.');
    } catch (e: any) {
      const errMsg = e.message || 'Error de conexión';
      this.banks.update(current => 
        current.map(b => b.code === code ? { ...b, error: errMsg } : b)
      );
      this.statusMessage.set(errMsg);
    } finally {
      this.isLoading.set(false);
    }
  }

  async confirmOTP() {
    const code = this.otpCode().trim();
    if (!code) return;
    
    const target = this.pendingQuery();
    this.showOTPModal.set(false);
    
    if (target === 'all') {
      await this.runAllQueries(code);
    } else if (target) {
      await this.runSingleQuery(target, code);
    }
    
    // Clean up
    this.otpCode.set('');
    this.pendingQuery.set(null);
  }

  saveConfig() {
    this.showSettingsModal.set(false);
    this.statusMessage.set('Credenciales guardadas provisionalmente.');
    setTimeout(() => this.statusMessage.set(''), 3000);
  }

  private parseNumeric(valueStr: string): number {
    if (!valueStr) return 0;
    let clean = valueStr.replace(/[^\d,.-]/g, '');
    if (clean.includes(',') && clean.includes('.')) {
      clean = clean.replace(/\./g, '').replace(/,/g, '.');
    } else if (clean.includes(',')) {
      clean = clean.replace(/,/g, '.');
    }
    const parsed = parseFloat(clean);
    return isNaN(parsed) ? 0 : parsed;
  }
}
