import { Component, input } from '@angular/core';
import { BankResponse, ExtractedData } from '../services/bank.service';

@Component({
  selector: 'app-bank-card',
  standalone: true,
  template: `
    <div class="bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800/80 rounded-3xl p-5 shadow-xs hover:shadow-md transition-all duration-300">
      <!-- Card Header -->
      <div class="flex flex-col gap-2 mb-4 pb-3 border-b border-zinc-50 dark:border-zinc-800/50">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-2xl flex items-center justify-center font-bold text-[10px] tracking-wider" [class]="getLogoClasses()">
              {{ getShortName() }}
            </div>
            <div>
              <h4 class="font-semibold text-zinc-900 dark:text-white leading-tight text-sm">{{ bank().label }}</h4>
              <span class="text-[10px] text-zinc-400 dark:text-zinc-500 font-mono">Cód: {{ bank().code }}</span>
            </div>
          </div>
          
          @if (isLoading()) {
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" [class]="getBadgeClasses()"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" [class]="getBadgeClasses()"></span>
            </span>
          } @else if (bank().error) {
            <span class="text-[9px] font-bold text-red-500 bg-red-50 dark:bg-red-950/20 px-2 py-0.5 rounded-full uppercase tracking-wider">Error</span>
          } @else {
            <span class="text-[9px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 px-2 py-0.5 rounded-full uppercase tracking-wider">Listo</span>
          }
        </div>

        @if (bank().config && bank().config!.length > 0) {
          <div class="flex flex-wrap gap-1.5 mt-1">
            @for (cfg of bank().config; track cfg.key) {
              <span class="text-[9px] bg-zinc-50 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 px-2 py-0.5 rounded-md font-medium border border-zinc-100 dark:border-zinc-700/30 flex items-center gap-1 select-none">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.2" stroke="currentColor" class="w-2.5 h-2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
                </svg>
                {{ cfg.label }}
              </span>
            }
          </div>
        }
      </div>

      <!-- Card Body / Balances -->
      @if (isLoading()) {
        <div class="flex flex-col gap-3 py-2 animate-pulse">
          <div class="h-4 bg-zinc-100 dark:bg-zinc-800 rounded w-2/3"></div>
          <div class="h-3 bg-zinc-100 dark:bg-zinc-800 rounded w-1/2"></div>
        </div>
      } @else if (bank().error) {
        <div class="py-2">
          <p class="text-xs text-red-500 dark:text-red-400 leading-relaxed">{{ bank().error }}</p>
        </div>
      } @else if (!bank().data || (isDataArray() && getArrayData().length === 0)) {
        <div class="py-4 text-center">
          <p class="text-xs text-zinc-400 dark:text-zinc-500">Sin datos de cuentas disponibles.</p>
        </div>
      } @else {
        @if (isDataString()) {
          <div class="flex items-center justify-between py-1">
            <span class="text-xs text-zinc-500 dark:text-zinc-400">Saldo Disponible</span>
            <span class="text-sm font-bold text-zinc-900 dark:text-white">{{ bank().data }}</span>
          </div>
        } @else {
          <div class="flex flex-col gap-2">
            @for (item of getArrayData(); track item.label) {
              <div class="flex flex-col gap-0.5 py-1.5 border-b border-zinc-50/50 dark:border-zinc-800/10 last:border-b-0">
                <div class="flex items-start justify-between gap-4">
                  <span class="text-xs text-zinc-500 dark:text-zinc-400 font-medium leading-tight max-w-[70%]">
                    {{ item.label }}
                  </span>
                  <span class="text-xs font-bold text-zinc-900 dark:text-white text-right whitespace-nowrap">
                    {{ item.value }}
                  </span>
                </div>
              </div>
            }
          </div>
        }
      }
    </div>
  `
})
export class BankCardComponent {
  bank = input.required<BankResponse>();
  isLoading = input<boolean>(false);

  getShortName(): string {
    const label = this.bank().label || '';
    if (label.toLowerCase().includes('nacional de credito') || label.toLowerCase().includes('bnc')) {
      return 'BNC';
    }
    if (label.toLowerCase().includes('bancamiga')) {
      return 'AMIGA';
    }
    return label.substring(0, 5).toUpperCase();
  }

  getLogoClasses(): string {
    const label = this.bank().label || '';
    if (label.toLowerCase().includes('bnc') || label.toLowerCase().includes('nacional de credito')) {
      return 'bg-blue-50 text-blue-600 dark:bg-blue-950/20 dark:text-blue-400';
    }
    if (label.toLowerCase().includes('bancamiga')) {
      return 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400';
    }
    return 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400';
  }

  getBadgeClasses(): string {
    const label = this.bank().label || '';
    if (label.toLowerCase().includes('bnc') || label.toLowerCase().includes('nacional de credito')) {
      return 'bg-blue-500';
    }
    return 'bg-emerald-500';
  }

  isDataArray(): boolean {
    return Array.isArray(this.bank().data);
  }

  isDataString(): boolean {
    return typeof this.bank().data === 'string';
  }

  getArrayData(): ExtractedData[] {
    return this.isDataArray() ? (this.bank().data as ExtractedData[]) : [];
  }
}
