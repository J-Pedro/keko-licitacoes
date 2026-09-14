import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../environments/environment';

export interface Licitacao {
  fonte: string;
  idExterno: string | null;
  orgao: string | null;
  cnpjOrgao: string | null;
  unidade: string | null;
  uf: string | null;
  municipio: string | null;
  modalidade: string | null;
  modalidadeId: number | null;
  objeto: string | null;
  numeroEdital: string | null;
  dataPublicacao: string | null;
  dataAberturaProposta: string | null;
  dataEncerramentoProposta: string | null;
  situacao: string | null;
  valorEstimado: number | null;
  sistemaOrigem: string | null;
  link: string | null;
  matchedKeywords?: string[];
}

export interface LicitacaoSearchError {
  palavraChave: string;
  mensagem: string;
}

export interface LicitacaoPage {
  pagina: number;
  tamanhoPagina: number;
  totalRegistros: number;
  totalPaginas: number;
  paginasRestantes: number;
  resultados: Licitacao[];
  erros?: LicitacaoSearchError[];
}

export interface LicitacaoSearchParams {
  palavraChave?: string;
  palavrasChave?: string[];
  uf?: string;
  modalidades?: number[];
  status?: string;
  tiposDocumento?: string;
  ordenacao?: string;
  pagina?: number;
  tamanhoPagina?: number;
}

@Injectable({ providedIn: 'root' })
export class LicitacoesService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  buscar(params: LicitacaoSearchParams): Observable<LicitacaoPage> {
    let httpParams = new HttpParams()
      .set('pagina', String(params.pagina ?? 1))
      .set('tamanhoPagina', String(params.tamanhoPagina ?? 10))
      .set('status', params.status || 'recebendo_proposta')
      .set('tiposDocumento', params.tiposDocumento || 'edital')
      .set('ordenacao', params.ordenacao || '-data');

    const palavrasChave = this.normalizarPalavrasChave(
      params.palavrasChave ?? (params.palavraChave ? [params.palavraChave] : [])
    );

    for (const palavraChave of palavrasChave) {
      httpParams = httpParams.append('palavraChave', palavraChave);
    }

    if (params.uf?.trim()) {
      httpParams = httpParams.set('uf', params.uf.trim().toUpperCase());
    }

    for (const modalidade of params.modalidades ?? []) {
      httpParams = httpParams.append('modalidade', String(modalidade));
    }

    return this.http.get<LicitacaoPage>(this.apiUrl, { params: httpParams });
  }

  private normalizarPalavrasChave(palavrasChave: string[]): string[] {
    const unicas = new Map<string, string>();

    for (const palavraChave of palavrasChave) {
      const normalizada = palavraChave.trim();
      const chave = normalizada.toLocaleLowerCase('pt-BR');

      if (normalizada && !unicas.has(chave)) {
        unicas.set(chave, normalizada);
      }
    }

    return [...unicas.values()];
  }
}
