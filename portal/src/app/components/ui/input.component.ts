import { Component, input, model } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="flex flex-col gap-1.5 w-full">
      @if (label()) {
        <label [for]="id()" class="text-xs font-semibold text-zinc-500 uppercase tracking-wider dark:text-zinc-400">
          {{ label() }}
        </label>
      }
      <div class="relative flex items-center">
        <input
          [id]="id()"
          [type]="type()"
          [placeholder]="placeholder()"
          [(ngModel)]="value"
          [disabled]="disabled()"
          class="w-full px-3.5 py-2.5 bg-zinc-50/50 border border-zinc-200/80 rounded-xl text-sm transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-900/60 dark:bg-zinc-900/30 dark:border-zinc-800 dark:text-white dark:focus:bg-zinc-900/50 dark:focus:ring-white/10 dark:focus:border-white/60 disabled:opacity-50 disabled:cursor-not-allowed"
        />
      </div>
    </div>
  `
})
export class InputComponent {
  id = input<string>('input-' + Math.random().toString(36).substring(2, 9));
  label = input<string>('');
  type = input<string>('text');
  placeholder = input<string>('');
  disabled = input<boolean>(false);
  value = model<string>('');
}
