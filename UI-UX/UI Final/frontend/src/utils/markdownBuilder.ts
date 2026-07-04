/**
 * Сборка Markdown из blocks.
 *
 * Блоки приходят из /documents/{id}/pages/{n}/content_md.
 * Для image-блоков content уже содержит `![alt](/api/v1/files/{key})` — спасибо бэкенду.
 *
 * Задача утилиты — просто склеить content блоков в единый markdown.
 */

/**
 * Склеивает content блоков страницы в markdown-строку.
 * Для image-блоков ссылка на картинку уже встроена в content.
 */
export function buildMarkdownFromBlocks(
  blocks: Array<{
    number?: number;
    type?: string;
    content?: string;
    image_key?: string;
    bbox?: unknown;
  }>,
): string {
  if (!blocks || blocks.length === 0) return '';

  return blocks
    .map((b) => (b.content ?? '').trim())
    .filter(Boolean)
    .join('\n\n');
}
