import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-button',
  standalone: true,
  template: `
    <button
      [disabled]="disabled() || loading()"
      (click)="click.emit($event)"
      [class]="'flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm ' + getVariantClass()"
    >
      @if (loading()) {
        <svg class="animate-spin h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      }
      <ng-content></ng-content>
    </button>
  `
})
export class ButtonComponent {
  variant = input<'primary' | 'secondary' | 'danger' | 'ghost'>('primary');
  disabled = input<boolean>(false);
  loading = input<boolean>(false);
  click = output<MouseEvent>();

  getVariantClass() {
    switch (this.variant()) {
      case 'primary':
        return 'bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-900 dark:hover:bg-zinc-100 shadow-sm';
      case 'secondary':
        return 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200 border border-zinc-200/60 dark:bg-zinc-800/40 dark:text-white dark:hover:bg-zinc-800 dark:border-zinc-700/50';
      case 'danger':
        return 'bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-950/20 dark:text-red-400 dark:hover:bg-red-950/30';
      case 'ghost':
        return 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/50 dark:hover:text-white';
    }
  }
}
