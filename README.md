# PAMS - Parent Athlete Management System

**System Vision: "Predictable Excellence"**

Build athlete predictability across physical, mental, and academic dimensions.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the system:
- **Parent Dashboard**: http://localhost:5000
- **Athlete App**: http://localhost:5000/athlete

## Core Features

### 🏆 Parent Dashboard
- Real-time metrics monitoring
- Weekly analytics and trends
- AI-powered insights and alerts
- Performance tracking across all domains

### ⚽ Athlete App
- Daily check-in form
- Sleep, mood, and training logging
- Hydration and nutrition tracking
- Gratitude and mindset exercises

### 📊 Tracked Domains
- **Athletic Training**: Consistency, completion rates
- **Nutrition**: Hydration levels, meal quality
- **Rest & Recovery**: Sleep hours, mood scores
- **Study & Focus**: Homework completion, academic discipline
- **Mental Balance**: Gratitude logging, emotional regulation

## Daily Rhythm Framework

| Time | Module | Action |
|------|--------|--------|
| 6:30 AM | Wake & Reflection | Sleep score, gratitude log |
| 7:00 AM | Nutrition | Balanced breakfast logging |
| 4:30 PM | Training | Session completion tracking |
| 8:30 PM | Mental Balance | Reflection + tomorrow's goals |
| 9:00 PM | Rest | Sleep tracking begins |

## Data Storage

Simple JSON file storage in `data/` directory:
- `checkins.json` - Daily check-in data
- Automatic backup and analytics generation

## AI Coach Features

- Predictive analytics for fatigue/injury risk
- Personalized nutrition recommendations
- Weekly performance reports with insights
- Automated alerts for concerning trends