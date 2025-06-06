# Office Room & Oasis Booking System

A clean, public-facing Streamlit application for office room and Oasis desk reservations.

## 🚀 Features

- **Public Interface**: Simple booking forms for teams and individuals
- **Real-time Display**: Always shows current allocations at the top
- **Team Bookings**: Reserve rooms for Monday/Wednesday or Tuesday/Thursday
- **Oasis Bookings**: Individual desk reservations for any weekday
- **Admin Controls**: Simple admin interface for data management and allocation

## 📱 User Interface

### What Users See:
1. **Current Allocations** (always visible at top)
   - Room allocation grid showing which teams are in which rooms
   - Oasis desk bookings by day

2. **Booking Forms**
   - Team room preference submission
   - Individual Oasis desk preference submission

### Admin Features:
- Clear all data (preferences and allocations)
- Run automatic room allocation algorithm
- Simple password-protected access

## 🛠️ Deployment

### Local Testing
```bash
cd new_strategy_allocation_tool
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push this folder to GitHub
2. Connect to Streamlit Cloud
3. Set up secrets in Streamlit Cloud dashboard:
   ```toml
   SUPABASE_DB_URI = "your_postgresql_connection_string"
   ADMIN_PASSWORD = "your_admin_password"
   OFFICE_TIMEZONE = "Europe/Amsterdam"
   ```

## ⚙️ Configuration

### Week Configuration
Change the current week in `app.py`:
```python
CURRENT_WEEK_MONDAY = date(2025, 6, 9)  # Change this date
```

### Room Configuration
Edit `rooms.json` to modify available rooms and capacities.

### Admin Password
Set via Streamlit secrets or environment variable `ADMIN_PASSWORD`.

## 🗄️ Database

Requires PostgreSQL with these tables:
- `weekly_preferences`: Team booking preferences
- `oasis_preferences`: Individual Oasis preferences  
- `weekly_allocations`: Assigned room allocations
- `oasis_allocations`: Assigned Oasis desk allocations

## 📋 Usage Flow

1. **Users visit the public site**
2. **View current allocations** (always visible)
3. **Submit preferences** using the forms
4. **Admin logs in** and runs allocation
5. **Updated allocations** are immediately visible to all users

Simple, clean, and public-facing! 🎯
