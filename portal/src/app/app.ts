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
  private socket?: WebSocket;

  // Signals for core state
  readonly banks = signal<BankResponse[]>([]);
  readonly isSyncingAll = signal<boolean>(false);
  readonly loadingBanks = signal<string[]>([]);
  readonly isLoadingAny = computed(() => this.isSyncingAll() || this.loadingBanks().length > 0);
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
    this.loadCachedBanks();
    this.loadInitialBanks();
    this.connectWebSocket();
  }

  isCardLoading(code: string): boolean {
    return this.isSyncingAll() || this.loadingBanks().includes(code);
  }

  private loadCachedBanks() {
    const cached = localStorage.getItem('cached_banks');
    if (cached) {
      try {
        const list = JSON.parse(cached);
        if (Array.isArray(list) && list.length > 0) {
          this.banks.set(list);
          console.log('Successfully loaded cached banks from localStorage.');
        }
      } catch (e) {
        console.warn('Could not parse cached banks from localStorage', e);
      }
    }
  }

  private saveToLocalStorage() {
    try {
      localStorage.setItem('cached_banks', JSON.stringify(this.banks()));
    } catch (e) {
      console.error('Could not save banks to localStorage', e);
    }
  }

  private connectWebSocket() {
    const wsUrl = 'ws://localhost:8000/api/ws/query';
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket connected successfully.');
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        if (data.action === 'request_otp') {
          this.pendingQuery.set(data.bank_code);
          this.showOTPModal.set(true);
          this.statusMessage.set(`Código 2FA requerido para ${data.label || 'Banco'}.`);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onclose = (event) => {
      console.log('WebSocket connection closed. Reconnecting in 3s...', event.reason);
      setTimeout(() => this.connectWebSocket(), 3000);
    };
  }

  private async loadInitialBanks() {
    try {
      this.statusMessage.set('Conectando con el servidor...');
      const data = await this.bankService.getBanks();
      const cachedList = this.banks();
      
      const formatted: BankResponse[] = data.map((b: any) => {
        const cachedBank = cachedList.find(x => x.code === b.code);
        return {
          label: b.label,
          code: b.code,
          config: b.config,
          data: cachedBank ? cachedBank.data : null,
          error: cachedBank ? cachedBank.error : undefined
        };
      });
      this.banks.set(formatted);
      this.saveToLocalStorage();
      this.statusMessage.set('');
    } catch (e) {
      console.warn('Could not connect to backend, loading default local banks.', e);
      this.fallbackBanks();
    }
  }

  private fallbackBanks() {
    const cachedList = this.banks();
    if (cachedList.length === 0) {
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
    }
    this.saveToLocalStorage();
    this.statusMessage.set('');
  }

  async runAllQueries(otp?: string) {
    if (this.isSyncingAll() || this.loadingBanks().length > 0) return;
    
    this.isSyncingAll.set(true);
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
      this.saveToLocalStorage();
      this.statusMessage.set('Cuentas actualizadas.');
    } catch (e: any) {
      this.statusMessage.set(`Error de conexión: ${e.message || e}`);
    } finally {
      this.isSyncingAll.set(false);
    }
  }

  async runSingleQuery(code: string, otp?: string) {
    if (this.isSyncingAll() || this.loadingBanks().includes(code)) return;
    
    this.loadingBanks.update(current => [...current, code]);
    const bank = this.banks().find(b => b.code === code);
    const bankName = bank?.label || 'Banco';
    this.statusMessage.set(`Consultando ${bankName}...`);
    
    this.banks.update(current => 
      current.map(b => b.code === code ? { ...b, error: undefined } : b)
    );

    try {
      const data = await this.bankService.queryByBank(code, otp);
      this.banks.update(current => {
        const updated = current.map(b => b.code === code ? { ...b, data, error: undefined } : b);
        setTimeout(() => this.saveToLocalStorage(), 0);
        return updated;
      });
      this.statusMessage.set('Actualizado.');
    } catch (e: any) {
      const errMsg = e.message || 'Error de conexión';
      this.banks.update(current => {
        const updated = current.map(b => b.code === code ? { ...b, error: errMsg } : b);
        setTimeout(() => this.saveToLocalStorage(), 0);
        return updated;
      });
      this.statusMessage.set(errMsg);
    } finally {
      this.loadingBanks.update(current => current.filter(c => c !== code));
    }
  }

  confirmOTP() {
    const code = this.otpCode().trim();
    if (!code) return;
    
    const target = this.pendingQuery();
    
    if (this.socket && this.socket.readyState === WebSocket.OPEN && target) {
      console.log(`Submitting 2FA code '${code}' for bank '${target}' via WebSocket...`);
      this.socket.send(JSON.stringify({
        action: 'submit_otp',
        bank_code: target,
        code: code
      }));
      this.statusMessage.set('Código enviado, procesando consulta...');
    } else {
      console.warn('Socket not open, falling back to query initialization...');
      if (target === 'all') {
        this.runAllQueries(code);
      } else if (target) {
        this.runSingleQuery(target, code);
      }
    }
    
    // Clean up
    this.showOTPModal.set(false);
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
