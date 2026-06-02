import React, { useState } from 'react';
import { 
  Dialog, 
  DialogContent, 
  Box, 
  Typography, 
  IconButton, 
  Button, 
  MobileStepper,
  Paper,
  Stack
} from '@mui/material';
import { X, ChevronRight, ChevronLeft, CheckCircle, MessageSquare, Search, Database, ClipboardCheck, BarChart3 } from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { motion, AnimatePresence } from 'motion/react';

const SCENES = [
  {
    title: 'Чат инженера',
    description: 'Задавайте вопросы на естественном языке. Система найдет ответы в базе ГОСТов, чертежей и спецификаций, предоставив точные цитаты.',
    icon: MessageSquare,
  },
  {
    title: 'Поиск и исследование',
    description: 'Профессиональный поиск по фрагментам текстов. Фильтруйте результаты по версии документа, типу и релевантности.',
    icon: Search,
  },
  {
    title: 'База знаний',
    description: 'Контролируйте статус обработки ваших документов. Система автоматически производит OCR и индексацию новых файлов.',
    icon: Database,
  },
  {
    title: 'Сверка параметров',
    description: 'Автоматическое выявление расхождений между разными версиями документов или чертежей для минимизации ошибок.',
    icon: ClipboardCheck,
  },
  {
    title: 'Мониторинг качества',
    description: 'Отслеживайте метрики точности ответов и качество распознавания текста в реальном времени.',
    icon: BarChart3,
  },
];

export const VideoGuideDialog: React.FC = () => {
  const { themeMode, videoGuideOpen, setVideoGuideOpen } = useUIStore();
  const [activeStep, setActiveStep] = useState(0);
  const isLight = themeMode === 'light';
  const SceneIcon = SCENES[activeStep].icon;

  const handleNext = () => setActiveStep((prev) => prev + 1);
  const handleBack = () => setActiveStep((prev) => prev - 1);

  return (
    <Dialog 
      fullScreen 
      open={videoGuideOpen} 
      onClose={() => setVideoGuideOpen(false)}
      slotProps={{
        paper: {
          sx: {
            bgcolor: 'background.default',
            background:
              isLight
                ? 'radial-gradient(circle at 18% 4%, rgba(56, 189, 248, 0.18), transparent 32%), linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)'
                : 'radial-gradient(circle at 22% 0%, rgba(112,161,255,0.12), transparent 30%), linear-gradient(135deg, #0b0c0e 0%, #11131a 48%, #0b0c0e 100%)',
          }
        }
      }}
    >
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <IconButton onClick={() => setVideoGuideOpen(false)} sx={{ color: 'text.secondary' }}>
          <X size={24} />
        </IconButton>
      </Box>

      <DialogContent
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          p: 4,
          pt: 2,
        }}
      >
        <Box
          sx={{
            maxWidth: 920,
            width: '100%',
            px: { xs: 2.5, md: 4.5 },
            py: { xs: 3, md: 4 },
            borderRadius: 4,
            border: isLight ? '1px solid rgba(15, 23, 42, 0.12)' : '1px solid rgba(255,255,255,0.10)',
            bgcolor: isLight ? 'rgba(255,255,255,0.88)' : 'rgba(22, 23, 27, 0.82)',
            boxShadow: isLight ? '0 24px 60px rgba(15,23,42,0.14)' : '0 24px 60px rgba(0,0,0,0.32)',
            backdropFilter: 'blur(16px)',
          }}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 4, alignItems: 'center' }}>
                <Box>
                  <Typography variant="overline" color="primary" sx={{ fontWeight: 700, letterSpacing: 2 }}>
                    Обучающая презентация
                  </Typography>
                  <Typography variant="h3" sx={{ mt: 1, mb: 3, fontWeight: 700 }}>
                    {SCENES[activeStep].title}
                  </Typography>
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 4, lineHeight: 1.6, fontWeight: 400 }}>
                    {SCENES[activeStep].description}
                  </Typography>
                  
                  {activeStep === SCENES.length - 1 ? (
                    <Button 
                      variant="contained" 
                      size="large" 
                      onClick={() => setVideoGuideOpen(false)}
                      startIcon={<CheckCircle size={20} />}
                      sx={{ px: 4, py: 1.5, borderRadius: 2 }}
                    >
                      Понятно, приступить к работе
                    </Button>
                  ) : (
                    <Button 
                      variant="contained" 
                      size="large" 
                      onClick={handleNext}
                      endIcon={<ChevronRight size={20} />}
                      sx={{ px: 4, py: 1.5, borderRadius: 2 }}
                    >
                      Далее
                    </Button>
                  )}
                </Box>
                <Box>
                  <Paper 
                    elevation={24} 
                    sx={{ 
                      borderRadius: 4, 
                      overflow: 'hidden', 
                      aspectRatio: '4/3', 
                      position: 'relative',
                      display: 'grid',
                      placeItems: 'center',
                      border: isLight ? '1px solid rgba(2, 132, 199, 0.18)' : '1px solid rgba(255,255,255,0.1)',
                      background: isLight
                        ? 'linear-gradient(145deg, #eff6ff 0%, #e0f2fe 52%, #f8fafc 100%)'
                        : 'linear-gradient(145deg, rgba(18,67,75,0.86), rgba(11,28,34,0.94))',
                    }}
                  >
                    <Box
                      sx={{
                        width: 156,
                        height: 156,
                        borderRadius: '44px',
                        display: 'grid',
                        placeItems: 'center',
                        color: isLight ? '#0284c7' : '#98d9d8',
                        bgcolor: isLight ? 'rgba(255,255,255,0.72)' : 'rgba(255,255,255,0.055)',
                        border: isLight ? '1px solid rgba(2,132,199,0.18)' : '1px solid rgba(152,217,216,0.18)',
                        boxShadow: isLight
                          ? '0 22px 45px rgba(2, 132, 199, 0.16)'
                          : '0 22px 45px rgba(0,0,0,0.28)',
                      }}
                    >
                      <SceneIcon size={76} strokeWidth={1.7} />
                    </Box>
                    <Typography
                      sx={{
                        position: 'absolute',
                        left: 24,
                        bottom: 22,
                        color: isLight ? '#075985' : 'rgba(230, 246, 247, 0.88)',
                        fontWeight: 700,
                        letterSpacing: '0.04em',
                      }}
                    >
                      {activeStep + 1} / {SCENES.length}
                    </Typography>
                  </Paper>
                </Box>
              </Box>
            </motion.div>
          </AnimatePresence>

          <Box sx={{ mt: 8 }}>
            <MobileStepper
              variant="progress"
              steps={SCENES.length}
              position="static"
              activeStep={activeStep}
              sx={{ 
                bgcolor: 'transparent', 
                flexGrow: 1,
                '& .MuiLinearProgress-root': { 
                  width: '100%', 
                  height: 6, 
                  borderRadius: 3,
                  bgcolor: isLight ? 'rgba(15,23,42,0.10)' : 'rgba(255,255,255,0.05)'
                },
                '& .MuiLinearProgress-bar': {
                  bgcolor: isLight ? '#0284c7' : '#c79b63',
                }
              }}
              nextButton={
                <IconButton size="small" onClick={handleNext} disabled={activeStep === SCENES.length - 1} sx={{ ml: 2 }}>
                  <ChevronRight size={24} />
                </IconButton>
              }
              backButton={
                <IconButton size="small" onClick={handleBack} disabled={activeStep === 0} sx={{ mr: 2 }}>
                  <ChevronLeft size={24} />
                </IconButton>
              }
            />
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};
