from .base import BaseAdminRepository
from HclsWebApi.models import CheckLogin, AdminLogin, AdminType

class DjangoAdminRepository(BaseAdminRepository):
    def get_all_checklogins(self):
        return CheckLogin.objects.all()

    def find_checklogin_by_email(self, email):
        return CheckLogin.objects.filter(email=email).first()

    def create_checklogin(self, email, username, password, phone, admin_type, created_by=None, created_at=None):
        chk = CheckLogin.objects.create(
            email=email,
            username=username,
            password=password,
            phone=phone,
            admin_type=admin_type,
            created_by=created_by,
        )
        # `CheckLogin` uses `created_on`, not `created_at`.
        # Keep the repository signature stable, but only backfill when a value is explicitly provided.
        if created_at is not None:
            CheckLogin.objects.filter(pk=chk.pk).update(created_on=created_at)
            chk.refresh_from_db(fields=['created_on'])
        return chk

    def create_adminlogin_from_check(self, checklogin):
        # safe id generation
        last = AdminLogin.objects.order_by('-Id').first()
        next_id = (last.Id + 1) if last else 1
        # map admin_type
        try:
            at_id = int(checklogin.admin_type)
        except Exception:
            at_id = 1 if str(checklogin.admin_type).upper().startswith('M') else 2
        admtype = AdminType.objects.filter(Id=at_id).first()

        # ensure Gender length fits AdminLogin field (max_length=10) — truncate if needed
        gender_val = getattr(checklogin, 'gender', '') or ''
        if len(gender_val) > 10:
            gender_val = gender_val[:10]

        admin = AdminLogin.objects.create(
            Id=next_id,
            Name=checklogin.username or checklogin.email,
            Gender=gender_val or 'Not spec',
            Password=checklogin.password,
            Phone=getattr(checklogin, 'phone', '') or '',
            Email=checklogin.email,
            Address=getattr(checklogin, 'address', '') or '',
            AdminType=admtype if admtype else None,
            Status=bool(getattr(checklogin, 'status', False)),
        )
        return admin

    def get_opadmin_items_and_counts(self):
        admins = CheckLogin.objects.all()
        opadmins = []
        active_count = 0
        inactive_count = 0

        for a in admins:
            if str(a.admin_type).upper().startswith('2') or str(a.admin_type).upper().startswith('OP') or str(a.admin_type).upper().startswith('O'):
                if a.status:
                    active_count += 1
                else:
                    inactive_count += 1

                creator = a.created_by
                created_by_name = creator.username if creator and getattr(creator, 'username', None) else (creator.email if creator else 'System')
                opadmins.append({
                    'id': a.id,
                    'name': a.username or a.email,
                    'role': 'OpAdmin',
                    'email': a.email,
                    'phone': a.phone,
                    'created_by': created_by_name,
                    'created_on': getattr(a, 'created_on', None),
                    'status': 'Active' if a.status else 'Inactive',
                })

        return opadmins, active_count, inactive_count
