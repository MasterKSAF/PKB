function safeFileName(value: string) {
  return value
    .replace(/[\\/:*?"<>|]/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 90);
}

export function downloadPreviewFile(fileName: string, content: string, extension = 'txt') {
  const normalizedExtension = extension.replace(/^\./, '').toLowerCase() || 'txt';
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = `${safeFileName(fileName) || 'document-preview'}.${normalizedExtension}`;
  link.click();
  URL.revokeObjectURL(url);
}
