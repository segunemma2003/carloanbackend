"""
Script to create an admin user for the AVTO LAIF backend.
Run this after deployment to create your first admin user.

Usage:
    python scripts/create_admin.py
    or
    railway run python scripts/create_admin.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker, init_db
from app.core.security import hash_password
from app.models.user import User, UserRole


async def create_admin_user():
    """Create an admin user."""
    # Initialize database
    await init_db()
    
    email = input("Enter admin email (default: admin@avtolaif.ru): ").strip() or "admin@avtolaif.ru"
    password = input("Enter admin password: ").strip()
    
    if not password:
        print("Error: Password is required")
        return
    
    name = input("Enter admin name (default: Admin): ").strip() or "Admin"
    
    async with async_session_maker() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User with email {email} already exists.")
            update = input("Do you want to update this user to admin? (y/n): ").strip().lower()
            if update == 'y':
                existing_user.role = UserRole.ADMIN
                existing_user.password_hash = hash_password(password)
                existing_user.is_active = True
                existing_user.email_verified = True
                await session.commit()
                print(f"✓ Updated user {email} to admin")
            else:
                print("Cancelled.")
            return
        
        # Create new admin user
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.ADMIN,
            is_active=True,
            email_verified=True,
            phone_verified=False,
        )
        
        session.add(admin_user)
        await session.commit()
        
        print(f"✓ Admin user created successfully!")
        print(f"  Email: {email}")
        print(f"  Name: {name}")
        print(f"  Role: ADMIN")
        print(f"\nYou can now log in to the admin panel at /admin")


if __name__ == "__main__":
    asyncio.run(create_admin_user())

