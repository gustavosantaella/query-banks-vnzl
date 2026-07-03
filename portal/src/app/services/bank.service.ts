import { Injectable } from '@angular/core';

export interface ExtractedData {
  label: string;
  value: string;
}

export interface BankConfig {
  label: string;
  key: string;
  required: boolean;
}

export interface BankResponse {
  label: string;
  code: string;
  data: ExtractedData[] | string | null;
  config?: BankConfig[];
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class BankService {
  private readonly API_BASE = 'http://localhost:8000/api/query';

  /**
   * Fetch all configured banks from the backend
   */
  async getBanks(): Promise<BankResponse[]> {
    const response = await fetch(`${this.API_BASE}/banks`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const res = await response.json();
    return res.data || [];
  }

  /**
   * Sync and fetch all bank queries
   */
  async queryAll(googleAuth?: string): Promise<BankResponse[]> {
    let url = `${this.API_BASE}/`;
    if (googleAuth) {
      url += `?google_auth=${encodeURIComponent(googleAuth)}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const res = await response.json();
    return res.data || [];
  }

  /**
   * Sync and fetch a single bank query by its code
   */
  async queryByBank(code: string, googleAuth?: string): Promise<ExtractedData[] | string | null> {
    let url = `${this.API_BASE}/by-bank?code=${code}`;
    if (googleAuth) {
      url += `&google_auth=${encodeURIComponent(googleAuth)}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const res = await response.json();
    return res.data;
  }
}
