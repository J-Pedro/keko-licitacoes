import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

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
}

export interface LicitacaoPage {
  pagina: number;
  tamanhoPagina: number;
  totalRegistros: number;
  totalPaginas: number;
  paginasRestantes: number;
  resultados: Licitacao[];
}

export interface LicitacaoSearchParams {
  palavraChave?: string;
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
  private readonly apiUrl = 'http://localhost:8080/api/licitacoes';

  buscar(params: LicitacaoSearchParams): Observable<LicitacaoPage> {
    let httpParams = new HttpParams()
      .set('pagina', String(params.pagina ?? 1))
      .set('tamanhoPagina', String(params.tamanhoPagina ?? 10))
      .set('status', params.status || 'recebendo_proposta')
      .set('tiposDocumento', params.tiposDocumento || 'edital')
      .set('ordenacao', params.ordenacao || '-data');

    if (params.palavraChave?.trim()) {
      httpParams = httpParams.set('palavraChave', params.palavraChave.trim());
    }

    if (params.uf?.trim()) {
      httpParams = httpParams.set('uf', params.uf.trim().toUpperCase());
    }

    for (const modalidade of params.modalidades ?? []) {
      httpParams = httpParams.append('modalidade', String(modalidade));
    }

    return this.http.get<LicitacaoPage>(this.apiUrl, { params: httpParams });
  }
}
