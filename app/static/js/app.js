
document.querySelectorAll('.thumb').forEach(button => {
  button.addEventListener('click', () => {
    const image = document.getElementById('mainImage');
    if (!image) return;
    image.src = button.dataset.src;
    document.querySelectorAll('.thumb').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
  });
});

const imageInput = document.querySelector('.drop-zone input[type=file]');
if (imageInput) {
  imageInput.addEventListener('change', () => {
    const preview = document.getElementById('uploadPreview');
    preview.innerHTML = '';
    Array.from(imageInput.files).slice(0, 3).forEach(file => {
      if (!file.type.startsWith('image/')) return;
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.onload = () => URL.revokeObjectURL(img.src);
      preview.appendChild(img);
    });
  });
}

setTimeout(() => {
  document.querySelectorAll('.flash').forEach(item => item.style.opacity = '0');
}, 3500);
