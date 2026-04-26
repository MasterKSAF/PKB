import React from 'react';
import { Box, Chip, Container, Divider, IconButton, Paper, Tooltip, Typography } from '@mui/material';
import { BadgeCheck, Clock3, Database, Info, ScanSearch, ShieldCheck, Terminal } from 'lucide-react';
import { MOCK_ENGINEER_RATINGS, MOCK_METRICS } from '../utils/mockData';

const cardSurface = {
  borderRadius: 3,
  bgcolor: 'rgba(16, 18, 24, 0.92)',
  border: '1px solid rgba(255,255,255,0.10)',
  boxShadow: '0 18px 40px rgba(0, 0, 0, 0.24)',
};

const controlMetrics = [
  {
    label: 'Качество OCR',
    value: `${MOCK_METRICS.ocrQuality}%`,
    target: 'цель не ниже 80%',
    state: MOCK_METRICS.ocrQuality >= 80 ? 'в норме' : 'ниже цели',
    ok: MOCK_METRICS.ocrQuality >= 80,
    icon: <Database size={18} />,
    accent: '#7edfa6',
    helper:
      'Доля страниц, где текст и базовая структура распознаны без критичных ошибок по контрольной выборке.',
  },
  {
    label: 'Качество поиска',
    value: `${MOCK_METRICS.retrievalQuality}%`,
    target: 'цель не ниже 85%',
    state: MOCK_METRICS.retrievalQuality >= 85 ? 'в норме' : 'ниже цели',
    ok: MOCK_METRICS.retrievalQuality >= 85,
    icon: <ScanSearch size={18} />,
    accent: '#89c3ff',
    helper:
      'Доля запросов, где нужный фрагмент найден в верхней части выдачи и пригоден для подготовки ответа.',
  },
  {
    label: 'Ответы с указанием страницы',
    value: `${MOCK_METRICS.answersWithSources}%`,
    target: 'цель 100%',
    state: MOCK_METRICS.answersWithSources >= 100 ? 'в норме' : 'ниже цели',
    ok: MOCK_METRICS.answersWithSources >= 100,
    icon: <ShieldCheck size={18} />,
    accent: '#d6c07f',
    helper:
      'Процент ответов, где есть ссылка на документ, страницу и цитируемый фрагмент. Для ТЗ это обязательный контроль.',
  },
  {
    label: 'Среднее время поиска',
    value: `${MOCK_METRICS.searchLatency} с`,
    target: 'цель не более 30 с',
    state: MOCK_METRICS.searchLatency <= 30 ? 'в норме' : 'выше цели',
    ok: MOCK_METRICS.searchLatency <= 30,
    icon: <Clock3 size={18} />,
    accent: '#a58cff',
    helper:
      'Среднее время от запроса до готовой подборки релевантных фрагментов. В ТЗ это входит в контроль скорости.',
  },
];

const answerMetrics = [
  {
    label: 'Полезные ответы',
    value: `${MOCK_ENGINEER_RATINGS.usefulRate}%`,
    note: 'по оценке инженеров',
    accent: '#a58cff',
    state: 'основная метрика',
    helper:
      'Доля ответов, которые инженер отметил как пригодные для работы без дополнительных замечаний.',
  },
  {
    label: 'Оценено ответов',
    value: `${MOCK_ENGINEER_RATINGS.ratedAnswers}`,
    note: 'уже попали в статистику',
    accent: '#8ec5ff',
    state: 'есть база оценки',
    helper:
      'Количество ответов, по которым инженер оставил оценку. Это база для тестовых и целевых прогонов.',
  },
  {
    label: 'На ручную проверку',
    value: `${MOCK_ENGINEER_RATINGS.flaggedForReview}`,
    note: 'кейсов отправлено на разбор',
    accent: '#d6c07f',
    state: 'нужен разбор',
    helper:
      'Число ответов, которые требуют ручной проверки из-за спорной страницы, версии документа или качества ответа.',
  },
  {
    label: 'Спорные после разбора',
    value: `${MOCK_ENGINEER_RATINGS.unresolvedAfterReview}`,
    note: 'кейса требуют повторного решения',
    accent: '#e39a86',
    state: 'открытые вопросы',
    helper:
      'Количество кейсов, которые остаются проблемными даже после первичной ручной проверки.',
  },
];

const logRows = [
  {
    time: '12:34:02',
    text: 'Поиск по запросу "сталь корпуса" завершен. Подобрано 5 документов.',
    color: '#9fd3ff',
  },
  {
    time: '12:34:05',
    text: 'Страница 45 документа "Спецификация-2" помечена как требующая проверки.',
    color: '#f0c36d',
  },
  {
    time: '12:34:10',
    text: 'Получена инженерная оценка: ответ полезен, замечаний нет.',
    color: 'rgba(217, 221, 229, 0.88)',
  },
  {
    time: '12:35:01',
    text: 'Переиндексация новой партии PDF завершена без ошибок.',
    color: 'rgba(217, 221, 229, 0.88)',
  },
  {
    time: '12:35:26',
    text: 'Среднее время поиска за час: 1.4 с. Отклонений не обнаружено.',
    color: '#c5afff',
  },
  {
    time: '12:35:43',
    text: 'Кейс 18 направлен на ручную проверку из-за расхождения версии документа.',
    color: '#f0c36d',
  },
  {
    time: '12:36:11',
    text: 'Ответ с источником подтвержден инженером и включен в контрольную выборку.',
    color: '#8fd4aa',
  },
];

const controlMetricsHelper = controlMetrics
  .map((metric, index) => `${index + 1}. ${metric.label}: ${metric.helper}`)
  .join('\n\n');

const answerMetricsHelper = answerMetrics
  .map((metric, index) => `${index + 1}. ${metric.label}: ${metric.helper}`)
  .join('\n\n');

const Helper: React.FC<{ title: string }> = ({ title }) => (
  <Tooltip
    title={<Box sx={{ whiteSpace: 'pre-line', maxWidth: 360 }}>{title}</Box>}
    arrow
    placement="top"
  >
    <IconButton size="small" sx={{ color: 'rgba(171, 159, 255, 0.82)', p: 0.2 }}>
      <Info size={15} />
    </IconButton>
  </Tooltip>
);

const metricTileBase = {
  height: 172,
  p: 1.55,
  borderRadius: 2.2,
  bgcolor: 'rgba(255,255,255,0.035)',
  border: '1px solid rgba(255,255,255,0.08)',
  display: 'flex',
  flexDirection: 'column' as const,
  justifyContent: 'space-between' as const,
};

type MetricTileProps = {
  icon: React.ReactNode;
  accent: string;
  value: string;
  label: string;
  subline: string;
  chipLabel: string;
  chipTone?: 'ok' | 'warn' | 'neutral';
};

const MetricTile: React.FC<MetricTileProps> = ({
  icon,
  accent,
  value,
  label,
  subline,
  chipLabel,
  chipTone = 'neutral',
}) => (
  <Box sx={metricTileBase}>
    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1.2 }}>
      <Box
        sx={{
          width: 34,
          height: 34,
          borderRadius: 2,
          display: 'grid',
          placeItems: 'center',
          bgcolor: `${accent}16`,
          color: accent,
          border: `1px solid ${accent}33`,
          flexShrink: 0,
        }}
      >
        {icon}
      </Box>
    </Box>

    <Typography
      sx={{
        mt: 1.9,
        fontSize: '1.72rem',
        lineHeight: 1,
        fontWeight: 520,
        color: 'rgba(242, 245, 249, 0.95)',
        letterSpacing: '-0.03em',
      }}
    >
      {value}
    </Typography>

    <Typography sx={{ mt: 0.85, fontSize: '0.8rem', color: 'rgba(233, 237, 243, 0.9)' }}>{label}</Typography>
    <Typography sx={{ mt: 0.3, fontSize: '0.72rem', color: 'rgba(171, 183, 201, 0.72)' }}>{subline}</Typography>

    <Box sx={{ pt: 1.25, display: 'flex', justifyContent: 'flex-start', mt: 'auto' }}>
      <Chip
        size="small"
        label={chipLabel}
        sx={{
          height: 24,
          color:
            chipTone === 'ok' ? '#a8efc0' : chipTone === 'warn' ? '#ffd1a4' : 'rgba(226, 231, 239, 0.9)',
          bgcolor:
            chipTone === 'ok'
              ? 'rgba(106, 196, 136, 0.12)'
              : chipTone === 'warn'
                ? 'rgba(240, 168, 87, 0.12)'
                : 'rgba(255,255,255,0.06)',
          border:
            chipTone === 'ok'
              ? '1px solid rgba(106, 196, 136, 0.24)'
              : chipTone === 'warn'
                ? '1px solid rgba(240, 168, 87, 0.24)'
                : '1px solid rgba(255,255,255,0.10)',
          '& .MuiChip-label': { px: 1, fontSize: '0.69rem' },
        }}
      />
    </Box>
  </Box>
);

export const Monitor: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' }, gap: 3 }}>
        <Paper sx={{ ...cardSurface, p: 2.4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 1.6 }}>
            <Typography sx={{ fontSize: '0.98rem', fontWeight: 500, color: 'rgba(233, 237, 243, 0.94)' }}>
              Контрольные метрики
            </Typography>
            <Helper title={controlMetricsHelper} />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' }, gap: 1.15 }}>
            {controlMetrics.map((metric) => (
              <MetricTile
                key={metric.label}
                icon={metric.icon}
                accent={metric.accent}
                value={metric.value}
                label={metric.label}
                subline={metric.target}
                chipLabel={metric.state}
                chipTone={metric.ok ? 'ok' : 'warn'}
              />
            ))}
          </Box>
        </Paper>

        <Paper
          sx={{
            ...cardSurface,
            p: 2.4,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 1.6 }}>
              <Typography sx={{ fontSize: '0.98rem', fontWeight: 500, color: 'rgba(233, 237, 243, 0.94)' }}>
                Оценка ответов ассистента
              </Typography>
              <Helper title={answerMetricsHelper} />
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' }, gap: 1.15 }}>
              {answerMetrics.map((metric) => (
                <MetricTile
                  key={metric.label}
                  icon={<BadgeCheck size={18} />}
                  accent={metric.accent}
                  value={metric.value}
                  label={metric.label}
                  subline={metric.note}
                  chipLabel={metric.state}
                  chipTone="neutral"
                />
              ))}
            </Box>
          </Box>
        </Paper>

        <Paper sx={{ ...cardSurface, p: 2.4, gridColumn: { xs: 'auto', md: '1 / -1' } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 1.4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.1 }}>
              <Terminal size={18} color="#a58cff" />
              <Typography sx={{ fontSize: '0.98rem', fontWeight: 500, color: 'rgba(233, 237, 243, 0.94)' }}>
                Журнал проверки
              </Typography>
            </Box>
            <Helper title="Последние события по поиску, переобработке, пометкам на проверку и инженерским оценкам." />
          </Box>

          <Divider sx={{ mb: 1.5, borderColor: 'rgba(255,255,255,0.08)' }} />

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 1.05,
              fontFamily: 'JetBrains Mono, Consolas, monospace',
              fontSize: '0.78rem',
            }}
          >
            {logRows.map((row) => (
              <Box key={`${row.time}-${row.text}`} sx={{ color: row.color, minHeight: 20 }}>
                <Box component="span" sx={{ color: 'rgba(160, 169, 184, 0.78)', mr: 1.1 }}>
                  {row.time}
                </Box>
                <Box component="span">{row.text}</Box>
              </Box>
            ))}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};
