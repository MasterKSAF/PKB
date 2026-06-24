import React from 'react';
import { Box, Chip, Container, Divider, IconButton, Paper, Tooltip, Typography } from '@mui/material';
import { BadgeCheck, Clock3, Database, Info, ScanSearch, ShieldCheck, Terminal } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useUIStore } from '../store/uiStore';
import { metricsApi } from '../utils/http';

const cardSurface = {
  borderRadius: 3,
  bgcolor: 'rgba(22, 23, 27, 0.72)',
  border: '1.5px solid rgba(198, 216, 240, 0.34)',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.045)',
};

const controlMetrics = [
  {
    label: 'Качество OCR',
    target: 'цель не ниже 80%',
    icon: <Database size={18} />,
    accent: '#7edfa6',
    helper:
      'Доля страниц, где текст и базовая структура распознаны без критичных ошибок по контрольной выборке.',
  },
  {
    label: 'Качество поиска',
    target: 'цель не ниже 85%',
    icon: <ScanSearch size={18} />,
    accent: '#89c3ff',
    helper:
      'Доля запросов, где нужный фрагмент найден в верхней части выдачи и пригоден для подготовки ответа.',
  },
  {
    label: 'Ответы с указанием страницы',
    target: 'цель 100%',
    icon: <ShieldCheck size={18} />,
    accent: '#d6c07f',
    helper:
      'Процент ответов, где есть ссылка на документ, страницу и цитируемый фрагмент. Для ТЗ это обязательный контроль.',
  },
  {
    label: 'Среднее время поиска',
    target: 'цель не более 30 с',
    icon: <Clock3 size={18} />,
    accent: '#a58cff',
    helper:
      'Среднее время от запроса до готовой подборки релевантных фрагментов. В ТЗ это входит в контроль скорости.',
  },
];

const answerMetrics = [
  {
    label: 'Полезные ответы',
    note: 'по оценке инженеров',
    accent: '#a58cff',
    state: 'основная метрика',
    helper:
      'Доля ответов, которые инженер отметил как пригодные для работы без дополнительных замечаний.',
  },
  {
    label: 'Оценено ответов',
    note: 'уже попали в статистику',
    accent: '#8ec5ff',
    state: 'есть база оценки',
    helper:
      'Количество ответов, по которым инженер оставил оценку. Это база для тестовых и целевых прогонов.',
  },
  {
    label: 'На ручную проверку',
    note: 'кейсов отправлено на разбор',
    accent: '#d6c07f',
    state: 'нужен разбор',
    helper:
      'Число ответов, которые требуют ручной проверки из-за спорной страницы, версии документа или качества ответа.',
  },
  {
    label: 'Спорные после разбора',
    note: 'кейса требуют повторного решения',
    accent: '#e39a86',
    state: 'открытые вопросы',
    helper:
      'Количество кейсов, которые остаются проблемными даже после первичной ручной проверки.',
  },
];

const controlMetricsHelper = controlMetrics
  .map((metric, index) => `${index + 1}. ${metric.label}: ${metric.helper}`)
  .join('\n\n');

const answerMetricsHelper = answerMetrics
  .map((metric, index) => `${index + 1}. ${metric.label}: ${metric.helper}`)
  .join('\n\n');

const Helper: React.FC<{ title: string }> = ({ title }) => {
  const { themeMode } = useUIStore();
  const isLight = themeMode === 'light';

  return (
    <Tooltip
      title={<Box sx={{ whiteSpace: 'pre-line', maxWidth: 360 }}>{title}</Box>}
      arrow
      placement="top"
    >
      <IconButton
        size="small"
        sx={{
          width: 24,
          height: 24,
          color: isLight ? '#475569' : 'rgba(226, 231, 239, 0.76)',
          border: isLight ? '1px solid rgba(71, 85, 105, 0.24)' : '1px solid rgba(226, 231, 239, 0.18)',
          bgcolor: isLight ? 'rgba(248, 250, 252, 0.72)' : 'rgba(255,255,255,0.035)',
          p: 0,
          '&:hover': {
            bgcolor: isLight ? 'rgba(226, 232, 240, 0.78)' : 'rgba(255,255,255,0.07)',
          },
        }}
      >
        <Info size={14} />
      </IconButton>
    </Tooltip>
  );
};

const metricTileBase = {
  height: 172,
  p: 1.55,
  borderRadius: 2.2,
  bgcolor: 'rgba(255,255,255,0.04)',
  border: '1.5px solid rgba(198, 216, 240, 0.24)',
  boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.035)',
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

    <Box sx={{ pt: 1, pb: 0.35, display: 'flex', justifyContent: 'flex-end', mt: 'auto' }}>
      <Chip
        className={`metric-state-chip metric-state-chip-${chipTone}`}
        size="small"
        label={chipLabel}
        sx={{
          height: 24,
          color: 'rgba(226, 231, 239, 0.88)',
          bgcolor: 'rgba(255,255,255,0.055)',
          border: '1px solid rgba(226, 231, 239, 0.13)',
          '& .MuiChip-label': { px: 1, fontSize: '0.69rem' },
        }}
      />
    </Box>
  </Box>
);

export const Monitor: React.FC = () => {
  const { themeMode, workMode } = useUIStore();
  const isLight = themeMode === 'light';
  const metricsQuery = useQuery({
    queryKey: ['gateway-metrics-dashboard', workMode],
    queryFn: metricsApi.dashboard,
    staleTime: 30_000,
  });

  const dashboard = metricsQuery.data ?? {
    control: {
      ocrQuality: 0,
      retrievalQuality: 0,
      answersWithSources: 0,
      manualReviewQueue: 0,
      searchLatency: 0,
    },
    answers: {
      ratedAnswers: 0,
      usefulRate: 0,
      flaggedForReview: 0,
      unresolvedAfterReview: 0,
      commonSignals: [],
    },
    logs: [],
  };

  const currentControlMetrics = controlMetrics.map((metric, index) => {
    const values = [
      {
        value: `${dashboard.control.ocrQuality}%`,
        state: dashboard.control.ocrQuality >= 80 ? 'в норме' : 'ниже цели',
        ok: dashboard.control.ocrQuality >= 80,
      },
      {
        value: `${dashboard.control.retrievalQuality}%`,
        state: dashboard.control.retrievalQuality >= 85 ? 'в норме' : 'ниже цели',
        ok: dashboard.control.retrievalQuality >= 85,
      },
      {
        value: `${dashboard.control.answersWithSources}%`,
        state: dashboard.control.answersWithSources >= 100 ? 'в норме' : 'ниже цели',
        ok: dashboard.control.answersWithSources >= 100,
      },
      {
        value: `${dashboard.control.searchLatency} с`,
        state: dashboard.control.searchLatency <= 30 ? 'в норме' : 'выше цели',
        ok: dashboard.control.searchLatency <= 30,
      },
    ];

    return { ...metric, ...values[index] };
  });

  const currentAnswerMetrics = answerMetrics.map((metric, index) => {
    const values = [
      { value: `${dashboard.answers.usefulRate}%` },
      { value: `${dashboard.answers.ratedAnswers}` },
      { value: `${dashboard.answers.flaggedForReview}` },
      { value: `${dashboard.answers.unresolvedAfterReview}` },
    ];

    return { ...metric, ...values[index] };
  });

  const currentLogRows = dashboard.logs.map((row) => ({
    time: row.time,
    text: row.text,
    color: row.level === 'ERROR' ? '#e39a86' : row.level === 'WARN' ? '#f0c36d' : 'rgba(217, 221, 229, 0.88)',
  }));

  return (
    <Container maxWidth={false} disableGutters sx={{ py: 3, width: '100%' }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' }, gap: 3 }}>
        <Paper sx={{ ...cardSurface, p: 2.4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, mb: 1.6 }}>
            <Typography sx={{ fontSize: '0.98rem', fontWeight: 500, color: 'rgba(233, 237, 243, 0.94)' }}>
              Контрольные метрики
            </Typography>
            <Helper title={controlMetricsHelper} />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' }, gap: 1.15 }}>
            {currentControlMetrics.map((metric) => (
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
              {currentAnswerMetrics.map((metric) => (
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
              <Terminal size={18} color={isLight ? '#475569' : 'rgba(226, 231, 239, 0.78)'} />
              <Typography sx={{ fontSize: '0.98rem', fontWeight: 500, color: 'rgba(233, 237, 243, 0.94)' }}>
                Журнал проверки
              </Typography>
            </Box>
            <Helper title="Последние события по поиску, переобработке, пометкам на проверку и инженерским оценкам." />
          </Box>

          <Divider sx={{ mb: 1.5, borderColor: 'rgba(198, 216, 240, 0.26)' }} />

          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 0,
              fontFamily: 'JetBrains Mono, Consolas, monospace',
              fontSize: '0.78rem',
              border: '1.5px solid rgba(198, 216, 240, 0.34)',
              borderRadius: 2.2,
              overflow: 'hidden',
              bgcolor: isLight ? '#ffffff' : 'rgba(22, 23, 27, 0.72)',
              boxShadow: isLight
                ? '0 0 0 1px rgba(15, 23, 42, 0.08)'
                : 'inset 0 1px 0 rgba(255,255,255,0.035)',
            }}
          >
            {currentLogRows.map((row, index) => (
              <Box
                key={`${row.time}-${row.text}`}
                sx={{
                  color: isLight ? '#1f2937' : 'rgba(207, 216, 229, 0.88)',
                  minHeight: 20,
                  fontWeight: isLight ? 500 : 400,
                  px: 1.35,
                  py: 0.95,
                  bgcolor: index % 2 === 0 ? (isLight ? 'rgba(15, 23, 42, 0.025)' : 'rgba(255,255,255,0.016)') : 'transparent',
                  borderBottom:
                    index === currentLogRows.length - 1
                      ? 'none'
                      : isLight
                        ? '1px solid rgba(15, 23, 42, 0.10)'
                        : '1px solid rgba(198, 216, 240, 0.20)',
                }}
              >
                <Box
                  component="span"
                  sx={{
                    color: isLight ? '#0f5f6f' : 'rgba(160, 169, 184, 0.78)',
                    mr: 1.1,
                    fontWeight: isLight ? 700 : 400,
                  }}
                >
                  {row.time}
                </Box>
                <Box component="span">{row.text}</Box>
              </Box>
            ))}
            {!currentLogRows.length && (
              <Box
                sx={{
                  px: 1.35,
                  py: 1.15,
                  color: 'rgba(171, 183, 201, 0.72)',
                  fontStyle: 'italic',
                  bgcolor: isLight ? 'rgba(15, 23, 42, 0.02)' : 'rgba(255,255,255,0.016)',
                }}
              >
                Журнал проверки пуст.
              </Box>
            )}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};
