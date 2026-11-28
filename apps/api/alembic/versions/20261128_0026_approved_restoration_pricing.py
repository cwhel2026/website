"""Approved restoration pricing profile; preserve historical records."""
from alembic import op

revision = "20261128_0026"
down_revision = "20261128_0025"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO pricing_profiles (id,name,version,notes,is_active,effective_from,created_at)
        SELECT gen_random_uuid(),'surfacecoat-approved-restoration',COALESCE(MAX(version),0)+1,
        'Approved restoration rates; materials are provisional allowances.',true,now(),now()
        FROM pricing_profiles
    """)
    op.execute("UPDATE pricing_profiles SET is_active=false WHERE name <> 'surfacecoat-approved-restoration'")
    op.execute("""
        INSERT INTO pricing_rules (id,profile_id,rule_type,surface_type,service_category,amount_gbp,percentage,label,is_active)
        SELECT gen_random_uuid(),p.id,v.kind::pricing_rule_type,v.surface::surface_type,
               v.category::service_category,v.amount,v.extra,v.label,true
        FROM pricing_profiles p CROSS JOIN (VALUES
          ('PER_SQM','TARMAC','RESTORATION',10,1.50,'approved'),
          ('PER_SQM','BLOCK_PAVING','RESTORATION',12,2.51,'approved'),
          ('PER_SQM','IMPRINTED_CONCRETE','RESTORATION',12,3.00,'approved-clear'),
          ('PER_SQM','IMPRINTED_CONCRETE','RESTORATION',14,2.97,'approved-colour'),
          ('MINIMUM_JOB',NULL,NULL,350,NULL,NULL),
          ('TRAVEL',NULL,NULL,0.45,25,NULL),
          ('VAT_RATE',NULL,NULL,20,NULL,NULL),
          ('MIN_CONTRIBUTION_MARGIN',NULL,NULL,35,NULL,NULL)
        ) AS v(kind,surface,category,amount,extra,label)
        WHERE p.name='surfacecoat-approved-restoration'
    """)
    op.execute("""
        INSERT INTO services (id,slug,name,description,category,surface_types,requires_washing,requires_coating,is_commercial,is_active,sort_order,created_at)
        VALUES
        (gen_random_uuid(),'tarmac-driveway-restoration','Tarmac driveway restoration','Pressure washing, preparation and Marl Coatings recolouring','RESTORATION','tarmac',true,true,false,true,0,now()),
        (gen_random_uuid(),'block-paving-cleaning-sealing','Block paving restoration','Pressure washing, kiln-dried sand and Marl clear wet-look sealer','RESTORATION','block_paving',true,true,false,true,1,now()),
        (gen_random_uuid(),'imprinted-concrete-restoration','Imprinted concrete clear restoration','Pressure washing, preparation and Creteprint clear sealer','RESTORATION','imprinted_concrete',true,true,false,true,2,now()),
        (gen_random_uuid(),'imprinted-concrete-colour-restoration','Imprinted concrete colour restoration','Pressure washing, preparation and Creteprint coloured sealer','RESTORATION','imprinted_concrete',true,true,false,true,3,now())
        ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name,description=EXCLUDED.description,
        surface_types=EXCLUDED.surface_types,requires_washing=true,requires_coating=true
    """)


def downgrade():
    op.execute("UPDATE pricing_profiles SET is_active=false WHERE name='surfacecoat-approved-restoration'")
    op.execute("UPDATE pricing_profiles SET is_active=true WHERE id=(SELECT id FROM pricing_profiles WHERE name<>'surfacecoat-approved-restoration' ORDER BY version DESC LIMIT 1)")
