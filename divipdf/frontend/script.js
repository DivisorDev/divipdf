// Tool click redirect setup

document.addEventListener("DOMContentLoaded", () => {
  const pdfTools = [
    { name: "PDF to Word", path: "../pdf-tools/pdf-to-word/index.html" },
    { name: "Word to PDF", path: "../pdf-tools/word-to-pdf/index.html" },
    { name: "Merge PDF", path: "../pdf-tools/merge-pdf/index.html" },
    { name: "Compress PDF", path: "../pdf-tools/compress-pdf/index.html" },
  ];
  const imageTools = [
    { name: "Image Compress (JPG/PNG/WEBP)", path: "../image-tools/compress/index.html" },
    { name: "Image Resize (Custom Dimension)", path: "../image-tools/resize/index.html" },
    { name: "Image to PDF", path: "../image-tools/to-pdf/index.html" },
    { name: "Convert Image Format (JPEG-PNG-WEBP)", path: "../image-tools/convert-format/index.html" },
    { name: "Remove Background", path: "../image-tools/remove-bg/index.html" },
    { name: "Watermark Remover", path: "../image-tools/remove-watermark/index.html" },
  ];

  const allTools = [...pdfTools, ...imageTools];

  // Assign click event to each list item
  document.querySelectorAll("ul li").forEach((item) => {
    const match = allTools.find(tool => item.textContent.trim() === tool.name);
    if (match) {
      item.style.cursor = "pointer";
      item.addEventListener("click", () => {
        window.location.href = match.path;
      });
    }

    // Hover effect animation
    item.addEventListener("mouseover", () => {
      item.style.transition = "transform 0.2s ease, color 0.3s";
      item.style.transform = "scale(1.05)";
    });
    item.addEventListener("mouseout", () => {
      item.style.transform = "scale(1)";
    });
  });
});
