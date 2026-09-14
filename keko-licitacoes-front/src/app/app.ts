import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { LicitacaoPage, LicitacoesService } from './licitacoes.service';

interface SelectOption {
  value: string;
  label: string;
}

interface EstadoOption {
  uf: string;
  nome: string;
}

interface ModalidadeOption {
  id: number;
  nome: string;
}

interface FiltrosBusca {
  palavraChave: string;
  uf: string;
  status: string;
  ordenacao: string;
  tamanhoPagina: number;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  private readonly licitacoesService = inject(LicitacoesService);

  protected readonly resultado = signal<LicitacaoPage | null>(null);
  protected readonly carregando = signal(false);
  protected readonly erro = signal<string | null>(null);
  protected readonly aviso = signal<string | null>(null);
  protected readonly modalidadesSelecionadas = signal<number[]>([]);
  protected readonly palavrasChave = signal<string[]>([]);

  protected readonly podeVoltar = computed(() => (this.resultado()?.pagina ?? 1) > 1);
  protected readonly podeAvancar = computed(() => (this.resultado()?.paginasRestantes ?? 0) > 0);

  protected filtros: FiltrosBusca = {
    palavraChave: '',
    uf: '',
    status: 'recebendo_proposta',
    ordenacao: '-data',
    tamanhoPagina: 10
  };

  protected readonly statusOptions: SelectOption[] = [
    { value: 'recebendo_proposta', label: 'Recebendo proposta' },
    { value: 'propostas_encerradas', label: 'Propostas encerradas' },
    { value: 'encerradas', label: 'Encerradas' },
    { value: 'todos', label: 'Todos' }
  ];

  protected readonly modalidades: ModalidadeOption[] = [
    { id: 6, nome: 'Pregao eletronico' },
    { id: 4, nome: 'Concorrencia eletronica' },
    { id: 8, nome: 'Dispensa' },
    { id: 9, nome: 'Inexigibilidade' },
    { id: 12, nome: 'Credenciamento' },
    { id: 15, nome: 'Chamada publica' }
  ];

  protected readonly estados: EstadoOption[] = [
    { uf: 'AC', nome: 'Acre' },
    { uf: 'AL', nome: 'Alagoas' },
    { uf: 'AP', nome: 'Amapa' },
    { uf: 'AM', nome: 'Amazonas' },
    { uf: 'BA', nome: 'Bahia' },
    { uf: 'CE', nome: 'Ceara' },
    { uf: 'DF', nome: 'Distrito Federal' },
    { uf: 'ES', nome: 'Espirito Santo' },
    { uf: 'GO', nome: 'Goias' },
    { uf: 'MA', nome: 'Maranhao' },
    { uf: 'MT', nome: 'Mato Grosso' },
    { uf: 'MS', nome: 'Mato Grosso do Sul' },
    { uf: 'MG', nome: 'Minas Gerais' },
    { uf: 'PA', nome: 'Para' },
    { uf: 'PB', nome: 'Paraiba' },
    { uf: 'PR', nome: 'Parana' },
    { uf: 'PE', nome: 'Pernambuco' },
    { uf: 'PI', nome: 'Piaui' },
    { uf: 'RJ', nome: 'Rio de Janeiro' },
    { uf: 'RN', nome: 'Rio Grande do Norte' },
    { uf: 'RS', nome: 'Rio Grande do Sul' },
    { uf: 'RO', nome: 'Rondonia' },
    { uf: 'RR', nome: 'Roraima' },
    { uf: 'SC', nome: 'Santa Catarina' },
    { uf: 'SP', nome: 'Sao Paulo' },
    { uf: 'SE', nome: 'Sergipe' },
    { uf: 'TO', nome: 'Tocantins' }
  ];

  protected pesquisar(pagina = 1): void {
    if (this.carregando()) {
      return;
    }

    this.carregando.set(true);
    this.erro.set(null);
    this.aviso.set(null);

    this.licitacoesService.buscar({
      ...this.filtros,
      palavraChave: '',
      palavrasChave: this.palavrasChave(),
      modalidades: this.modalidadesSelecionadas(),
      pagina
    }).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
        this.aviso.set(this.mensagemErroParcial(resultado));
        this.carregando.set(false);
      },
      error: () => {
        this.erro.set('Nao foi possivel consultar o PNCP agora. Confira se a API esta rodando e tente novamente.');
        this.carregando.set(false);
      }
    });
  }

  protected limpar(): void {
    this.filtros = {
      palavraChave: '',
      uf: '',
      status: 'recebendo_proposta',
      ordenacao: '-data',
      tamanhoPagina: 10
    };
    this.modalidadesSelecionadas.set([]);
    this.palavrasChave.set([]);
    this.resultado.set(null);
    this.erro.set(null);
    this.aviso.set(null);
  }

  protected adicionarPalavraChave(): void {
    const palavraChave = this.filtros.palavraChave.trim();

    if (!palavraChave) {
      return;
    }

    const jaExiste = this.palavrasChave().some(
      (palavra) => palavra.toLocaleLowerCase('pt-BR') === palavraChave.toLocaleLowerCase('pt-BR')
    );

    if (jaExiste) {
      this.filtros.palavraChave = '';
      return;
    }

    this.palavrasChave.set([...this.palavrasChave(), palavraChave]);
    this.filtros.palavraChave = '';
  }

  protected removerPalavraChave(palavraChave: string): void {
    this.palavrasChave.set(this.palavrasChave().filter((palavra) => palavra !== palavraChave));
  }

  protected adicionarPalavraChaveComEnter(event: KeyboardEvent): void {
    if (event.key !== 'Enter') {
      return;
    }

    event.preventDefault();
    this.adicionarPalavraChave();
  }

  protected alternarModalidade(id: number, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const atuais = this.modalidadesSelecionadas();
    this.modalidadesSelecionadas.set(
      checked ? [...atuais, id] : atuais.filter((modalidadeId) => modalidadeId !== id)
    );
  }

  protected paginaAnterior(): void {
    const paginaAtual = this.resultado()?.pagina ?? 1;
    if (paginaAtual > 1) {
      this.pesquisar(paginaAtual - 1);
    }
  }

  protected proximaPagina(): void {
    const paginaAtual = this.resultado()?.pagina ?? 1;
    if (this.podeAvancar()) {
      this.pesquisar(paginaAtual + 1);
    }
  }

  protected formatarData(valor: string | null): string {
    if (!valor) {
      return '-';
    }

    const data = new Date(valor);
    if (Number.isNaN(data.getTime())) {
      return valor;
    }

    return new Intl.DateTimeFormat('pt-BR').format(data);
  }

  protected formatarMoeda(valor: number | null): string {
    if (valor === null || valor === undefined) {
      return '-';
    }

    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      maximumFractionDigits: 2
    }).format(valor);
  }

  private mensagemErroParcial(resultado: LicitacaoPage): string | null {
    const erros = resultado.erros ?? [];

    if (!erros.length) {
      return null;
    }

    if (!resultado.resultados.length) {
      return 'Nenhuma palavra-chave pode ser consultada no PNCP agora. Tente novamente em alguns instantes.';
    }

    const palavras = erros.map((erro) => erro.palavraChave).join(', ');
    return `Uma ou mais palavras-chave nao puderam ser consultadas: ${palavras}. Os demais resultados foram mantidos.`;
  }

  protected textoCarregando(): string {
    const total = this.palavrasChave().length;

    if (total > 1) {
      return `Consultando ${total} palavras-chave no PNCP...`;
    }

    return 'Consultando o PNCP...';
  }
}
