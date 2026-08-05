/**
 * Scripts auxiliares do marketplace.
 */

// Gerenciador de arquivos selecionados para upload
let dtUpload = new DataTransfer();

function previewImagens(input) {
    const container = document.getElementById('preview-container');
    if (!container) return;

    if (input.files && input.files.length > 0) {
        for (let file of input.files) {
            let existe = false;
            for (let f of dtUpload.files) {
                if (f.name === file.name && f.size === file.size) {
                    existe = true;
                    break;
                }
            }
            if (!existe) {
                dtUpload.items.add(file);
            }
        }
        input.files = dtUpload.files;
    }

    renderizarPreviews();
}

function removerImagemDoUpload(index) {
    const input = document.getElementById('imagens');
    const novoDt = new DataTransfer();

    for (let i = 0; i < dtUpload.files.length; i++) {
        if (i !== index) {
            novoDt.items.add(dtUpload.files[i]);
        }
    }

    dtUpload = novoDt;
    if (input) {
        input.files = dtUpload.files;
    }
    renderizarPreviews();
}

function limparTodasImagens() {
    dtUpload = new DataTransfer();
    const input = document.getElementById('imagens');
    if (input) {
        input.files = dtUpload.files;
    }
    renderizarPreviews();
}

function renderizarPreviews() {
    const container = document.getElementById('preview-container');
    if (!container) return;
    container.innerHTML = '';

    const files = dtUpload.files;
    if (files.length === 0) return;

    // Header de ações rápidas
    const infoHeader = document.createElement('div');
    infoHeader.className = 'w-full flex items-center justify-between text-xs text-slate-500 mb-2';
    infoHeader.innerHTML = `
        <span><strong>${files.length}</strong> foto(s) selecionada(s)</span>
        <button type="button" onclick="limparTodasImagens()" class="text-red-600 hover:text-red-700 font-semibold">
            Remover todas
        </button>
    `;
    container.appendChild(infoHeader);

    const grid = document.createElement('div');
    grid.className = 'flex gap-3 flex-wrap w-full';
    container.appendChild(grid);

    Array.from(files).forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.className = 'img-preview-card relative group w-24 h-24 rounded-xl overflow-hidden border-2 border-slate-200 shadow-sm shrink-0 bg-slate-100';
            div.style.cssText = 'position: relative; display: inline-block; width: 96px; height: 96px; border-radius: 12px; overflow: hidden; border: 2px solid rgba(0,0,0,0.06);';
            div.innerHTML = `
                <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;" alt="${file.name}">
                <button type="button"
                        onclick="removerImagemDoUpload(${index})"
                        title="Remover esta foto"
                        class="btn-remover-foto"
                        style="position: absolute; top: 4px; right: 4px; z-index: 50; background-color: #ff3b30; color: #ffffff; border: none; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
                    <svg style="width: 10px; height: 10px;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
                <span style="position: absolute; bottom: 4px; left: 4px; z-index: 40; background-color: rgba(0,0,0,0.55); color: #ffffff; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                    ${index + 1}
                </span>
            `;
            grid.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

// Galeria de imagens no detalhe do imóvel
function trocarImagemPrincipal(src, thumbnail) {
    const principal = document.getElementById('imagem-principal');
    if (principal) {
        principal.src = src;
        // Remove active de todos os thumbnails
        document.querySelectorAll('.thumbnail-img').forEach(t => {
            t.classList.remove('thumbnail-active');
            t.classList.add('opacity-60');
        });
        // Marca o clicado como ativo
        thumbnail.classList.add('thumbnail-active');
        thumbnail.classList.remove('opacity-60');
    }
}

// Toggle dos filtros na busca (mobile)
function toggleFiltros() {
    const filtros = document.getElementById('filtros-container');
    if (filtros) {
        filtros.classList.toggle('hidden');
    }
}

// Formata preço no formato brasileiro
function formatarPreco(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 0,
    }).format(valor);
}

// Confirmação de exclusão
function confirmarExclusao(formId) {
    if (confirm('Tem certeza que deseja excluir este imóvel? Esta ação não pode ser desfeita.')) {
        document.getElementById(formId).submit();
    }
}
