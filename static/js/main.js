/**
 * Scripts auxiliares do marketplace.
 */

// Preview de imagens antes do upload
function previewImagens(input) {
    const container = document.getElementById('preview-container');
    if (!container) return;
    container.innerHTML = '';

    if (input.files) {
        Array.from(input.files).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const div = document.createElement('div');
                div.className = 'relative group';
                div.innerHTML = `
                    <img src="${e.target.result}"
                         class="w-24 h-24 object-cover rounded-lg border-2 border-slate-200"
                         alt="Preview ${index + 1}">
                    <span class="absolute bottom-1 right-1 bg-black/60 text-white text-xs px-1 rounded">
                        ${index + 1}
                    </span>
                `;
                container.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    }
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
