-- Fix RLS on System Tables
-- Migration: 20261114085038_fix_system_rls
-- Enables RLS on roles, user_roles, permissions, role_permissions

ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;

-- Roles: authenticated users can read all roles
CREATE POLICY "Authenticated users can read roles" ON public.roles
    FOR SELECT TO authenticated USING (true);

-- Permissions: authenticated users can read all permissions
CREATE POLICY "Authenticated users can read permissions" ON public.permissions
    FOR SELECT TO authenticated USING (true);

-- User Roles: authenticated users can read all user_roles (for admin checks)
-- Users can also view their own roles
CREATE POLICY "Authenticated users can read user_roles" ON public.user_roles
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Users can view own roles" ON public.user_roles
    FOR SELECT TO authenticated USING (user_id = auth.uid());

-- Role Permissions: authenticated users can read all role_permissions
CREATE POLICY "Authenticated users can read role_permissions" ON public.role_permissions
    FOR SELECT TO authenticated USING (true);