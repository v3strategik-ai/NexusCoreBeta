#!/usr/bin/env python3
"""
Phase 6C Data Migration Script
Adds required enterprise fields to existing collections for multi-tenant compatibility
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/nexus_core')
DEFAULT_TENANT_ID = "default-tenant"
DEFAULT_USER_ID = "system-migration"

class Phase6CMigration:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGO_URL)
            # Extract database name from URL
            db_name = MONGO_URL.split('/')[-1] if '/' in MONGO_URL else 'nexus_core'
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("🔒 Database connection closed")
    
    async def create_default_tenant(self):
        """Create a default tenant for existing data"""
        try:
            # Check if default tenant already exists
            existing_tenant = await self.db.tenants.find_one({"id": DEFAULT_TENANT_ID})
            
            if not existing_tenant:
                default_tenant = {
                    "_id": DEFAULT_TENANT_ID,
                    "id": DEFAULT_TENANT_ID,
                    "name": "Default Organization",
                    "subdomain": "default",
                    "status": "active",
                    "plan_type": "enterprise",
                    "max_users": 1000,
                    "max_agents": 500,
                    "current_users": 1,
                    "current_agents": 0,
                    "storage_used_mb": 0.0,
                    "admin_email": "admin@default.com",
                    "billing_email": None,
                    "phone": None,
                    "address": None,
                    "branding": {
                        "company_name": "Default Organization",
                        "primary_color": "#3b82f6",
                        "logo_url": None
                    },
                    "settings": {},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await self.db.tenants.insert_one(default_tenant)
                logger.info(f"✅ Created default tenant: {DEFAULT_TENANT_ID}")
            else:
                logger.info(f"ℹ️  Default tenant already exists: {DEFAULT_TENANT_ID}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create default tenant: {e}")
            return False
    
    async def create_default_user(self):
        """Create a default system user for migration purposes"""
        try:
            # Check if default user already exists
            existing_user = await self.db.users.find_one({"id": DEFAULT_USER_ID})
            
            if not existing_user:
                default_user = {
                    "_id": DEFAULT_USER_ID,
                    "id": DEFAULT_USER_ID,
                    "tenant_id": DEFAULT_TENANT_ID,
                    "email": "system@migration.local",
                    "username": "system-migration",
                    "password_hash": "system_account_no_login",
                    "first_name": "System",
                    "last_name": "Migration",
                    "avatar_url": None,
                    "phone": None,
                    "role": "super_admin",
                    "permissions": [],
                    "is_active": True,
                    "is_verified": True,
                    "last_login": None,
                    "preferences": {},
                    "login_count": 0,
                    "failed_login_attempts": 0,
                    "last_failed_login": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await self.db.users.insert_one(default_user)
                logger.info(f"✅ Created default user: {DEFAULT_USER_ID}")
            else:
                logger.info(f"ℹ️  Default user already exists: {DEFAULT_USER_ID}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create default user: {e}")
            return False
    
    async def migrate_collection(self, collection_name, batch_size=1000):
        """Migrate a collection to add enterprise fields"""
        try:
            collection = self.db[collection_name]
            
            # Count documents missing tenant_id
            missing_count = await collection.count_documents({
                "$or": [
                    {"tenant_id": {"$exists": False}},
                    {"created_by": {"$exists": False}},
                    {"updated_by": {"$exists": False}}
                ]
            })
            
            if missing_count == 0:
                logger.info(f"ℹ️  Collection '{collection_name}': All documents already migrated")
                return True
            
            logger.info(f"🔄 Migrating collection '{collection_name}': {missing_count} documents need updates")
            
            # Process in batches to avoid memory issues
            updated_count = 0
            cursor = collection.find({
                "$or": [
                    {"tenant_id": {"$exists": False}},
                    {"created_by": {"$exists": False}},
                    {"updated_by": {"$exists": False}}
                ]
            }).batch_size(batch_size)
            
            batch_updates = []
            
            async for document in cursor:
                doc_id = document.get("_id")
                update_fields = {}
                
                # Add tenant_id if missing
                if "tenant_id" not in document:
                    update_fields["tenant_id"] = DEFAULT_TENANT_ID
                
                # Add created_by if missing
                if "created_by" not in document:
                    update_fields["created_by"] = DEFAULT_USER_ID
                
                # Add updated_by if missing
                if "updated_by" not in document:
                    update_fields["updated_by"] = DEFAULT_USER_ID
                
                # Always update the updated_at timestamp for migrated records
                update_fields["updated_at"] = datetime.utcnow()
                
                if update_fields:
                    batch_updates.append({
                        "filter": {"_id": doc_id},
                        "update": {"$set": update_fields}
                    })
                
                # Execute batch update when batch size reached
                if len(batch_updates) >= batch_size:
                    result = await self.execute_batch_update(collection, batch_updates)
                    updated_count += result
                    batch_updates = []
                    logger.info(f"   📈 Progress: {updated_count}/{missing_count} documents updated")
            
            # Execute remaining updates
            if batch_updates:
                result = await self.execute_batch_update(collection, batch_updates)
                updated_count += result
            
            logger.info(f"✅ Collection '{collection_name}': {updated_count} documents migrated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate collection '{collection_name}': {e}")
            return False
    
    async def execute_batch_update(self, collection, batch_updates):
        """Execute a batch of updates"""
        try:
            from pymongo import UpdateOne
            
            operations = []
            for update in batch_updates:
                operations.append(
                    UpdateOne(
                        update["filter"],
                        update["update"]
                    )
                )
            
            if operations:
                result = await collection.bulk_write(operations)
                return result.modified_count
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
            return 0
    
    async def validate_migration(self):
        """Validate that migration was successful"""
        try:
            logger.info("🔍 Validating migration results...")
            
            collections_to_check = ['agents', 'leads', 'workflows', 'documents', 'knowledge_files']
            all_valid = True
            
            for collection_name in collections_to_check:
                collection = self.db[collection_name]
                
                # Check for documents missing required fields
                missing_tenant = await collection.count_documents({"tenant_id": {"$exists": False}})
                missing_created = await collection.count_documents({"created_by": {"$exists": False}})
                missing_updated = await collection.count_documents({"updated_by": {"$exists": False}})
                
                total_docs = await collection.count_documents({})
                
                if missing_tenant > 0 or missing_created > 0 or missing_updated > 0:
                    logger.error(f"❌ Collection '{collection_name}': Missing fields detected")
                    logger.error(f"   Missing tenant_id: {missing_tenant}/{total_docs}")
                    logger.error(f"   Missing created_by: {missing_created}/{total_docs}")
                    logger.error(f"   Missing updated_by: {missing_updated}/{total_docs}")
                    all_valid = False
                else:
                    logger.info(f"✅ Collection '{collection_name}': All {total_docs} documents have required fields")
            
            return all_valid
            
        except Exception as e:
            logger.error(f"❌ Migration validation failed: {e}")
            return False
    
    async def run_full_migration(self):
        """Run complete Phase 6C migration"""
        logger.info("🚀 Starting Phase 6C Enterprise Architecture Migration")
        logger.info("=" * 60)
        
        try:
            # Step 1: Connect to database
            if not await self.connect():
                return False
            
            # Step 2: Create default tenant and user
            logger.info("\n📋 Step 1: Setting up default enterprise entities...")
            if not await self.create_default_tenant():
                return False
            
            if not await self.create_default_user():
                return False
            
            # Step 3: Migrate all collections
            logger.info("\n📋 Step 2: Migrating existing collections...")
            collections_to_migrate = ['agents', 'leads', 'workflows', 'documents', 'knowledge_files']
            
            for collection_name in collections_to_migrate:
                if not await self.migrate_collection(collection_name):
                    logger.error(f"❌ Migration failed for collection: {collection_name}")
                    return False
            
            # Step 4: Validate migration
            logger.info("\n📋 Step 3: Validating migration...")
            if not await self.validate_migration():
                logger.error("❌ Migration validation failed")
                return False
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 Phase 6C Migration Completed Successfully!")
            logger.info("✅ All existing data is now enterprise-ready")
            logger.info("✅ Multi-tenant architecture fully operational")
            logger.info("✅ Role-based access control ready")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        
        finally:
            await self.close()

async def main():
    """Main migration function"""
    migration = Phase6CMigration()
    success = await migration.run_full_migration()
    
    if success:
        print("\n🎯 Migration completed successfully!")
        print("The application is now ready for Phase 6C enterprise features.")
    else:
        print("\n💥 Migration failed!")
        print("Please check the logs and fix any issues before proceeding.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())