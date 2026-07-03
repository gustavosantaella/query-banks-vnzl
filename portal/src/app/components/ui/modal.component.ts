import { Component, input, output, model } from '@angular/core';

@Component({
  selector: 'app-modal',
  standalone: true,
  template: `
    @if (isOpen()) {
      <div class="fixed inset-0 z-50 flex items-end justify-center sm:items-center p-4">
        <!-- Backdrop -->
        <div 
          class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300"
          (click)="close()"
        ></div>
        
        <!-- Drawer / Modal Body -->
        <div 
          class="relative w-full max-w-md bg-white dark:bg-zinc-900 rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl z-10 transition-transform duration-300 border border-zinc-100 dark:border-zinc-800 max-h-[85vh] overflow-y-auto"
        >
          <!-- Pull bar for mobile -->
          <div class="flex justify-center sm:hidden mb-4 -mt-2">
            <div class="w-12 h-1 bg-zinc-200 dark:bg-zinc-800 rounded-full"></div>
          </div>
          
          <div class="flex items-start justify-between mb-5">
            <h3 class="text-lg font-semibold text-zinc-950 dark:text-white">{{ title() }}</h3>
            <button 
              (click)="close()" 
              class="p-1.5 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors cursor-pointer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div class="py-1">
            <ng-content></ng-content>
          </div>
        </div>
      </div>
    }
  `
})
export class ModalComponent {
  title = input<string>('');
  isOpen = model<boolean>(false);
  closed = output<void>();

  close() {
    this.isOpen.set(false);
    this.closed.emit();
  }
}
