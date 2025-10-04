# MySQL Migration Guide

This guide will help you migrate your real estate platform from Firestore to MySQL, making it compatible with cPanel hosting.

## Prerequisites

1. **cPanel MySQL Database**: You need access to a cPanel account with MySQL database privileges
2. **Python Environment**: Ensure you have Python 3.8+ installed
3. **Backup**: Always backup your current Firestore data before migration

## Step 1: Set Up MySQL Database in cPanel

1. **Create Database**:
   - Log into your cPanel
   - Go to "MySQL Databases"
   - Create a new database (e.g., `yourusername_real_estate`)
   - Note down the database name

2. **Create Database User**:
   - Create a new MySQL user
   - Assign a strong password
   - Add the user to the database with "All Privileges"

3. **Note Connection Details**:
   - Host: Usually `localhost` (or your cPanel host)
   - Port: Usually `3306`
   - Database name: `yourusername_real_estate`
   - Username: `yourusername_dbuser`
   - Password: The password you set

## Step 2: Install Dependencies

```bash
# Install MySQL dependencies
pip install aiomysql PyMySQL

# Or install all requirements
pip install -r requirements.txt
```

## Step 3: Configure Environment

1. **Copy the example environment file**:
   ```bash
   cp env.mysql.example .env
   ```

2. **Update `.env` with your cPanel MySQL credentials**:
   ```env
   # Database Type
   DATABASE_TYPE=mysql
   
   # MySQL Configuration (cPanel compatible)
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=your_cpanel_username
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_cpanel_username_real_estate
   
   # Keep your existing Telegram and admin settings
   TELEGRAM_BOT_TOKEN=your_existing_token
   ADMIN_PHONE_NUMBER=your_existing_phone
   SECRET_KEY=your_existing_secret
   ```

## Step 4: Set Up Database Schema

1. **Import the database schema**:
   - In cPanel, go to "phpMyAdmin"
   - Select your database
   - Go to "Import" tab
   - Upload the `database_schema.sql` file
   - Click "Go" to execute

2. **Verify tables were created**:
   You should see these tables:
   - `users`
   - `user_roles`
   - `properties`
   - `property_images`
   - `cars`
   - `car_images`

## Step 5: Migrate Data (Optional)

If you have existing Firestore data, run the migration script:

```bash
# Make sure your .env is configured for both Firestore and MySQL
python migrate_to_mysql.py
```

**Note**: The migration script will:
- Copy all users from Firestore to MySQL
- Copy all properties and their images
- Copy all cars and their images
- Preserve all relationships and data integrity

## Step 6: Test the Migration

1. **Start your application**:
   ```bash
   python -m uvicorn src.app.main:app --reload
   ```

2. **Test key functionality**:
   - User registration/login
   - Property submission
   - Property filtering
   - Admin functions

## Step 7: Deploy to cPanel

1. **Upload your code** to your cPanel file manager
2. **Set up Python environment** in cPanel (if supported)
3. **Configure environment variables** in your hosting panel
4. **Set up cron jobs** for any scheduled tasks

## Database Schema Overview

### Core Tables

- **users**: User accounts with roles and authentication
- **user_roles**: Many-to-many relationship for user roles
- **properties**: Property listings with full details
- **property_images**: Property images with ordering
- **cars**: Car listings with specifications
- **car_images**: Car images with ordering

### Key Features

- **Optimized Indexes**: Fast queries for filtering and search
- **Foreign Key Constraints**: Data integrity
- **UTF8MB4 Support**: Full Unicode support for international content
- **cPanel Compatible**: Works with standard cPanel MySQL setup

## Performance Optimizations

The MySQL schema includes:

1. **Strategic Indexes**: For common query patterns
2. **Composite Indexes**: For complex filtering
3. **Views**: For easier querying of approved content
4. **Connection Pooling**: Efficient database connections

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Check your MySQL host and port
   - Verify user permissions
   - Ensure MySQL service is running

2. **Authentication Failed**:
   - Double-check username and password
   - Verify user has proper privileges

3. **Database Not Found**:
   - Ensure database name is correct
   - Check if database exists in cPanel

4. **Migration Issues**:
   - Run migration script with debug output
   - Check Firestore credentials are still valid
   - Verify MySQL schema is properly imported

### Debug Mode

To run with debug output:
```bash
LOG_LEVEL=DEBUG python migrate_to_mysql.py
```

## Rollback Plan

If you need to rollback to Firestore:

1. Set `DATABASE_TYPE=firestore` in your `.env`
2. Restart your application
3. Your original Firestore data will be used

## Support

The MySQL implementation maintains 100% compatibility with your existing:
- API endpoints
- Telegram bot functionality
- Frontend integration
- Business logic

No changes are needed to your frontend or API consumers.

## Benefits of MySQL Migration

1. **Cost Effective**: No Firestore usage charges
2. **cPanel Compatible**: Works with standard hosting
3. **Better Performance**: Optimized queries and indexing
4. **Full Control**: Complete database management
5. **Backup Friendly**: Standard SQL backup procedures
6. **Scalable**: Can handle high traffic loads
