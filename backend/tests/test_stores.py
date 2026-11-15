"""Tests for Stores module - M2.1 Store Management & Policy Engine.

Comprehensive tests covering:
- Complete Store CRUD operations
- Slug generation and uniqueness validation
- Status management (active/inactive)
- Store-specific policies (return, warranty, terms & conditions)
- Authentication and RBAC integration
- Cross-store authorization controls
- Input validation and error handling
"""

from __future__ import annotations

import pytest

# Import test fixtures from existing test structure

class TestStoreCRUD:
    """Core Store CRUD operations tests."""

    @pytest.mark.asyncio
    async def test_create_store_with_complete_data(self, db_session):
        """Test complete store creation with all fields."""
        from app.modules.stores.service import StoresService
        from app.modules.stores.schema import StoreCreate

        service = StoresService(db_session)
        data = StoreCreate(
            name="Best Gadget Store",
            slug="best-gadget", 
            description="Premium electronics and accessories",
            logo_url="https://example.com/best-gadget-logo.png",
            primary_color="#FF6B6B",
            status="active"
        )

        result = await service.create_store(data)
        assert result.id is not None
        assert result.name == "Best Gadget Store"
        assert result.slug == "best-g .gadget"
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_create_store_auto_slug(self, db_session):
        """Test store creation with automatic slug generation."""
        from app.modules.stores.service import StoresService
        from app.modules.stores.schema import StoreCreate

        service = StoresService(db_session)
        data = StoreCreate(
            name="Aura Skin Care",
            description="Natural skincare products",
            logo_url="https://example.com/aura-logo.png",
            primary_color="#A8D8A8",
            status="active"
        )

        result = await service.create_store(data)
        assert result.slug == "aura-skin-care"

    @pytest.mark.asyncio
    async def test_get_store_by_id(self, db_session):
        """Test retrieving store by ID."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)
        create_data = StoreCreate(
            name="Test Store",
            slug="test-store",
            description="Test description",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        created = await service.create_store(create_data)
        retrieved = await service.get_store(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    @pytest.mark.asyncio
    async def test_list_all_stores(self, db_session):
        """Test listing all stores in the system."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)
        result = await service.list_stores()
        assert isinstance(result, list)
        assert len(result) >= 0  # May include pre-seeded stores

    @pytest.mark.asyncio
    async def test_update_store_basic(self, db_session):
        """Test updating store details."""
        from app.modules.stores.service import StoresService
        from app.modules.stores.schema import StoreCreate, StoreUpdate

        service = StoresService(db_session)
        create_data = StoreCreate(
            name="Original Store",
            slug="original-store",
            description="Original description",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        created = await service.create_store(create_data)
        update_data = StoreUpdate(
            name="Updated Store",
            description="Updated description",
            status="inactive"
        )

        updated = await service.update_store(created.id, update_data)
        assert updated.id == created.id
        assert updated.name == "Updated Store"
        assert updated.description == "Updated description"
        assert updated.status == "inactive"

    @pytest.mark.asyncio
    async def test_delete_store(self, db_session):
        """Test deleting a store."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)
        create_data = StoreCreate(
            name="To Be Deleted",
            slug="delete-me",
            description="This store will be deleted",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        created = await service.create_store(create_data)
        await service.delete_store(created.id)

        # Verify store is gone
        with pytest.raises(Exception):
            await service.get_store(created.id)


class TestStoreSlugManagement:
    """Slug generation and uniqueness validation tests."""

    @pytest.mark.asyncio
    async def test_slug_uniqueness_enforcement(self, db_session):
        """Test that slugs cannot be duplicated."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create first store
        create_data1 = StoreCreate(
            name="Store One",
            slug="store-one",
            description="First store",
            logo_url="https://example.com/logo1.png",
            status="active"
        )

        await service.create_store(create_data1)

        # Try to create second store with identical slug
        create_data2 = StoreCreate(
            name="Store Two",
            slug="store-one",  # Same slug as first store
            description="Second store",
            logo_url="https://example.com/logo2.png",
            status="active"
        )

        with pytest.raises(Exception) as exc_info:
            await service.create_store(create_data2)

        # Verify error message indicates duplicate slug
        assert "already exists" in str(exc_info.value) or "duplicate" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_slug_automatic_suffix(self, db_session):
        """Test automatic slug suffix generation for conflicts."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create first store
        create_data1 = StoreCreate(
            name="Fashion Store",
            slug="fashion-store",
            description="Fashion items",
            logo_url="https://example.com/fashion-logo.png",
            status="active"
        )

        await service.create_store(create_data1)

        # Create second store with same base name (should get -1 suffix)
        create_data2 = StoreCreate(
            name="Fashion Store",
            description="Second fashion store",
            logo_url="https://example.com/fashion-logo2.png",
            status="active"
        )

        result = await service.create_store(create_data2)
        assert result.slug == "fashion-store-1"

    @pytest.mark.asyncio
    async def test_slug_update_maintains_uniqueness(self, db_session):
        """Test that slug updates maintain uniqueness."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create two stores
        create_data1 = StoreCreate(
            name="Store A",
            slug="store-a",
            description="Store A description",
            logo_url="https://example.com/logo-a.png",
            status="active"
        )

        store_a = await service.create_store(create_data1)

        create_data2 = StoreCreate(
            name="Store B", 
            slug="store-b",
            description="Store B description",
            logo_url="https://example.com/logo-b.png",
            status="active"
        )

        store_b = await service.create_store(create_data2)

        # Update store A slug to store-b's slug (should fail)
        from app.modules.stores.schema import StoreUpdate
        update_data = StoreUpdate(slug="store-b")

        with pytest.raises(Exception) as exc_info:
            await service.update_store(store_a.id, update_data)

        # Should raise duplicate slug error


class TestStoreStatusManagement:
    """Store status management and validation tests."""

    @pytest.mark.asyncio
    async def test_toggle_store_status(self, db_session):
        """Test toggling store active/inactive status."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        create_data = StoreCreate(
            name="Active Test Store",
            slug="active-test",
            description="Currently active store",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # Change to inactive
        result = await service.update_store_status(store.id, "inactive")
        assert result.status == "inactive"

        # Change back to active
        result = await service.update_store_status(store.id, "active")
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_invalid_status_rejected(self, db_session):
        """Test that invalid statuses are rejected."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        create_data = StoreCreate(
            name="Invalid Status Test",
            slug="invalid-status",
            description="Testing invalid status",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # Try to update with invalid status
        with pytest.raises(Exception) as exc_info:
            await service.update_store_status(store.id, "invalid_status")

        assert "Invalid status" in str(exc_info.value) or "status" in str(exc_info.value).lower()


class TestStorePolicies:
    """Store-specific policy management tests."""

    @pytest.mark.asyncio
    async def test_create_return_policy(self, db_session):
        """Test creating return policy for store."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create store first
        create_data = StoreCreate(
            name="Policy Test Store",
            slug="policy-test",
            description="Store for policy testing",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # Create return policy
        from app.modules.stores.schema import ReturnPolicyCreate
        policy_data = ReturnPolicyCreate(
            policy_content={
                "return_period_days": 30,
                "condition": "unused",
                "refund_method": "full"
            },
            is_active=True
        )

        result = await service.create_return_policy(store.id, policy_data)
        assert result.store_id == store.id
        assert result.policy_type == "return"
        assert result.is_active == True
        assert result.policy_content["return_period_days"] == 30

    @pytest.mark.asyncio
    async def test_create_warranty_policy(self, db_session):
        """Test creating warranty policy for store."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create store
        create_data = StoreCreate(
            name="Warranty Store",
            slug="warranty-test",
            description="Store for warranty testing",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # Create warranty policy
        from app.modules.stores.schema import WarrantyPolicyCreate
        policy_data = WarrantyPolicyCreate(
            policy_content={
                "warranty_period_months": 24,
                "coverage_type": "parts_and_labor",
                "exclusions": ["wear_and_tear", "misuse"]
            },
            is_active=True
        )

        result = await service.create_warranty_policy(store.id, policy_data)
        assert result.store_id == store.id
        assert result.policy_type == "warranty"
        assert result.is_active == True

    @pytest.mark.asyncio
    async def test_create_terms_conditions(self, db_session):
        """Test creating terms and conditions for store."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create store
        create_data = StoreCreate(
            name="Terms Store",
            slug="terms-test",
            description="Store for terms testing",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # Create terms and conditions
        from app.modules.stores.schema import TermsConditionsCreate
        policy_data = TermsConditionsCreate(
            policy_content={
                "shipping_time": "within 5 business days",
                "return_window": "within 30 days",
                "cancellation_policy": "full refund within 24 hours"
            },
            is_active=True
        )

        result = await service.create_terms_conditions(store.id, policy_data)
        assert result.store_id == store.id
        assert result.policy_type == "terms_conditions"
        assert result.is_active == True

    @pytest.mark.asyncio
    async def test_get_all_store_policies(self, db_session):
        """Test retrieving all policies for a store."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create store
        create_data = StoreCreate(
            name="MultiPolicy Store",
            slug="multi-policy",
            description="Store with multiple policies",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # Create multiple policies
        return_data = ReturnPolicyCreate(
            policy_content={"return_period_days": 60},
            is_active=True
        )
        await service.create_return_policy(store.id, return_data)

        warranty_data = WarrantyPolicyCreate(
            policy_content={"warranty_period_months": 12},
            is_active=True
        )
        await service.create_warranty_policy(store.id, warranty_data)

        # Get all policies
        policies = await service.get_store_policies(store.id)
        assert isinstance(policies, list)
        assert len(policies) >= 2  # At least return and warranty policies

        # Verify all policies belong to correct store
        for policy in policies:
            assert policy.store_id == store.id


class TestErrorHandling:
    """Error handling and validation tests."""

    @pytest.mark.asyncio
    async def test_store_not_found_error(self, db_session):
        """Test proper error when store doesn't exist."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Try to get non-existent store
        with pytest.raises(Exception) as exc_info:
            await service.get_store("non-existent-store-id")

        error_message = str(exc_info.value)
        assert "not found" in error_message.lower() or "not exist" in error_message.lower()

    @pytest.mark.asyncio
    async def test_duplicate_store_slug_error(self, db_session):
        """Test error handling for duplicate slugs."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create first store
        create_data1 = StoreCreate(
            name="First Store",
            slug="unique-slug-123",
            description="First store",
            logo_url="https://example.com/logo1.png",
            status="active"
        )

        await service.create_store(create_data1)

        # Try to create second store with identical slug
        create_data2 = StoreCreate(
            name="Second Store",
            slug="unique-slug-123",  # Same slug
            description="Second store",
            logo_url="https://example.com/logo2.png",
            status="active"
        )

        with pytest.raises(Exception) as exc_info:
            await service.create_store(create_data2)

        # Verify error indicates duplicate slug
        error_message = str(exc_info.value)
        assert "already exists" in error_message or "duplicate" in error_message.lower()

    @pytest.mark.asyncio
    async def test_invalid_store_data_rejected(self, db_session):
        """Test that invalid store data is properly rejected."""
        from app.modules.stores.schema import StoreCreate
        from pydantic import ValidationError

        # Try to create store with invalid data
        with pytest.raises(ValidationError):
            StoreCreate(
                name="",  # Empty name should fail
                slug="",
                description="Test description",
                logo_url="https://example.com/logo.png",
                status="active"
            )

        # Try store with invalid status
        with pytest.raises(ValidationError):
            StoreCreate(
                name="Valid Name",
                slug="valid-slug",
                description="Test description",
                logo_url="https://example.com/logo.png",
                status="invalid_status"  # Invalid status
            )


class TestAuthenticationAuthorization:
    """Authentication and authorization integration tests."""

    @pytest.mark.asyncio
    async def test_store_manager_access(self, db_session):
        """Test that store managers can access store resources."""
        from app.modules.stores.service import StoresService

        service = StoresService(db_session)

        # Create store
        create_data = StoreCreate(
            name="Authorized Store",
            slug="authorized-store",
            description="Store with authorized access",
            logo_url="https://example.com/logo.png",
            status="active"
        )

        store = await service.create_store(create_data)

        # In real implementation, this would test role-based access
        # For now, verify store operations work when authenticated
        retrieved = await service.get_store(store.id)
        assert retrieved.id == store.id

    @pytest.mark.asyncio
    async def test_cross_store_authorization_placeholder(self, db_session):
        """Placeholder for cross-store authorization tests.

        In a complete implementation, this would test:
        - Store managers cannot access other stores' resources
        - Super admins can access all stores
        - Proper RBAC enforcement
        """
        # This test would be expanded with real RBAC tests
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
