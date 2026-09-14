import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { App } from './app';
import { LicitacaoPage, LicitacoesService } from './licitacoes.service';

const paginaVazia: LicitacaoPage = {
  pagina: 1,
  tamanhoPagina: 10,
  totalRegistros: 0,
  totalPaginas: 0,
  paginasRestantes: 0,
  resultados: []
};

describe('App', () => {
  let buscar: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    buscar = vi.fn().mockReturnValue(of(paginaVazia));

    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        {
          provide: LicitacoesService,
          useValue: { buscar }
        }
      ]
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render title', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Consulta de editais PNCP');
  });

  it('should add a trimmed keyword chip', async () => {
    const fixture = TestBed.createComponent(App);
    const app = componente(fixture);
    fixture.detectChanges();

    app.filtros.palavraChave = '  notebook dell  ';
    app.adicionarPalavraChave();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(textosDosChips(fixture.nativeElement)).toEqual(['notebook dell x']);
    expect(inputPalavraChave(fixture.nativeElement).value).toBe('');
  });

  it('should add a keyword with Enter without submitting the form', async () => {
    const fixture = TestBed.createComponent(App);
    const app = componente(fixture);
    fixture.detectChanges();

    app.filtros.palavraChave = 'monitor';
    app.adicionarPalavraChaveComEnter(new KeyboardEvent('keydown', { key: 'Enter', cancelable: true }));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(textosDosChips(fixture.nativeElement)).toEqual(['monitor x']);
    expect(buscar).not.toHaveBeenCalled();
  });

  it('should remove a keyword chip', async () => {
    const fixture = TestBed.createComponent(App);
    const app = componente(fixture);
    fixture.detectChanges();

    app.filtros.palavraChave = 'computador';
    app.adicionarPalavraChave();
    fixture.detectChanges();
    await fixture.whenStable();

    app.removerPalavraChave('computador');
    fixture.detectChanges();
    await fixture.whenStable();

    expect(textosDosChips(fixture.nativeElement)).toEqual([]);
  });

  it('should not add empty or duplicated keywords', async () => {
    const fixture = TestBed.createComponent(App);
    const app = componente(fixture);
    fixture.detectChanges();

    app.filtros.palavraChave = '   ';
    app.adicionarPalavraChave();
    app.filtros.palavraChave = 'Notebook';
    app.adicionarPalavraChave();
    app.filtros.palavraChave = 'notebook';
    app.adicionarPalavraChave();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(textosDosChips(fixture.nativeElement)).toEqual(['Notebook x']);
  });

  it('should search only with added keyword chips', async () => {
    const fixture = TestBed.createComponent(App);
    const app = componente(fixture);
    fixture.detectChanges();

    app.filtros.palavraChave = 'notebook';
    app.adicionarPalavraChave();
    app.filtros.palavraChave = 'texto nao adicionado';
    fixture.detectChanges();
    await fixture.whenStable();

    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(buscar).toHaveBeenCalledWith(
      expect.objectContaining({
        palavraChave: '',
        palavrasChave: ['notebook']
      })
    );
  });

  it('should render one keyword chip per matched keyword in the result card', async () => {
    buscar.mockReturnValue(of({
      ...paginaVazia,
      totalRegistros: 1,
      resultados: [
        {
          fonte: 'PNCP',
          idExterno: '1',
          orgao: 'Orgao',
          cnpjOrgao: null,
          unidade: null,
          uf: 'MG',
          municipio: 'Belo Horizonte',
          modalidade: 'Pregao - Eletronico',
          modalidadeId: 6,
          objeto: 'Compra de equipamentos',
          numeroEdital: '1/2026',
          dataPublicacao: '2026-09-05',
          dataAberturaProposta: null,
          dataEncerramentoProposta: null,
          situacao: 'Divulgado no PNCP',
          valorEstimado: null,
          sistemaOrigem: 'edital',
          link: null,
          matchedKeywords: ['material de construcao', 'equipamento']
        }
      ]
    }));

    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();

    const chips = [...fixture.nativeElement.querySelectorAll('.notice-meta span')].map((chip) =>
      (chip as HTMLElement).textContent?.trim()
    );
    expect(chips).toContain('material de construcao');
    expect(chips).toContain('equipamento');
  });
});

function inputPalavraChave(element: HTMLElement): HTMLInputElement {
  return element.querySelector('#palavraChave') as HTMLInputElement;
}

function textosDosChips(element: HTMLElement): string[] {
  return [...element.querySelectorAll('.keyword-chip')].map((chip) => (chip as HTMLElement).textContent?.trim() ?? '');
}

interface AppTeste {
  filtros: { palavraChave: string };
  adicionarPalavraChave(): void;
  adicionarPalavraChaveComEnter(event: KeyboardEvent): void;
  removerPalavraChave(palavraChave: string): void;
}

function componente(fixture: { componentInstance: App }): AppTeste {
  return fixture.componentInstance as unknown as AppTeste;
}
