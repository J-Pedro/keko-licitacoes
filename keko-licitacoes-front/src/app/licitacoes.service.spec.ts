import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../environments/environment';
import { Licitacao, LicitacaoPage, LicitacoesService } from './licitacoes.service';

describe('LicitacoesService', () => {
  let service: LicitacoesService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()]
    });

    service = TestBed.inject(LicitacoesService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('should send one palavraChave parameter per added keyword and keep the other filters', () => {
    service.buscar({
      palavrasChave: [' notebook ', 'monitor'],
      uf: 'mg',
      modalidades: [6, 4],
      status: 'todos',
      tiposDocumento: 'edital',
      ordenacao: '-data',
      pagina: 2,
      tamanhoPagina: 25
    }).subscribe();

    const request = http.expectOne((req) => req.url === environment.apiUrl);

    expect(request.request.params.getAll('palavraChave')).toEqual(['notebook', 'monitor']);
    expect(request.request.params.get('uf')).toBe('MG');
    expect(request.request.params.getAll('modalidade')).toEqual(['6', '4']);
    expect(request.request.params.get('status')).toBe('todos');
    expect(request.request.params.get('tiposDocumento')).toBe('edital');
    expect(request.request.params.get('ordenacao')).toBe('-data');
    expect(request.request.params.get('pagina')).toBe('2');
    expect(request.request.params.get('tamanhoPagina')).toBe('25');

    request.flush(paginaCom([]));
  });

  it('should ignore empty and duplicated keyword parameters case-insensitively', () => {
    service.buscar({
      palavrasChave: ['Notebook', ' ', 'notebook', 'Monitor']
    }).subscribe();

    const request = http.expectOne((req) => req.url === environment.apiUrl);

    expect(request.request.params.getAll('palavraChave')).toEqual(['Notebook', 'Monitor']);
    request.flush(paginaCom([]));
  });

  it('should not use a typed keyword when the keyword list is explicitly empty', () => {
    service.buscar({
      palavraChave: 'nao deve ir',
      palavrasChave: []
    }).subscribe();

    const request = http.expectOne((req) => req.url === environment.apiUrl);

    expect(request.request.params.has('palavraChave')).toBe(false);
    request.flush(paginaCom([]));
  });
});

function paginaCom(resultados: Licitacao[]): LicitacaoPage {
  return {
    pagina: 1,
    tamanhoPagina: 10,
    totalRegistros: resultados.length,
    totalPaginas: 0,
    paginasRestantes: 0,
    resultados
  };
}
