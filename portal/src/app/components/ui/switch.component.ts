import { Component, input, model } from '@angular/core';

@Component({
  selector: 'app-switch',
  standalone: true,
  template: `
    <div class="flex items-center justify-between gap-4 w-full">
      @if (label()) {
        <div class="flex flex-col">
          <span class="text-sm font-medium text-zinc-900 dark:text-white">{{ label() }}</span>
          @if (description()) {
            <span class="text-xs text-zinc-500 dark:text-zinc-400">{{ description() }}</span>
          }
        </div>
      }
      <button
        type="button"
        [disabled]="disabled()"
        (click)="toggle()"
        [class]="'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:ring-offset-2 dark:focus:ring-white disabled:opacity-50 disabled:cursor-not-allowed ' + (checked() ? 'bg-zinc-900 dark:bg-white' : 'bg-zinc-200 dark:bg-zinc-800')"
      >
        <span
          aria-hidden="true"
          [class]="'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white dark:bg-zinc-950 shadow ring-0 transition duration-200 ease-in-out ' + (checked() ? 'translate-x-5' : 'translate-x-0')"
        ></span>
      </button>
    </div>
  `
})
export class SwitchComponent {
  label = input<string>('');
  description = input<string>('');
  disabled = input<boolean>(false);
  checked = model<boolean>(false);

  toggle() {
    if (!this.disabled()) {
      this.checked.set(!this.checked());
    }
  }
}
