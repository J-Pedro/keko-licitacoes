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
  protected readonly modalidadesSelecionadas = signal<number[]>([]);

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
    this.carregando.set(true);
    this.erro.set(null);

    this.licitacoesService.buscar({
      ...this.filtros,
      modalidades: this.modalidadesSelecionadas(),
      pagina
    }).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
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
    this.resultado.set(null);
    this.erro.set(null);
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
}
