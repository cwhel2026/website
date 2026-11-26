
CREATE TYPE public.ad_platform AS ENUM (
    'META',
    'GOOGLE',
    'FLYER',
    'ORGANIC'
);

CREATE TYPE public.agent_task_status AS ENUM (
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED',
    'AWAITING_APPROVAL'
);

CREATE TYPE public.appointment_status AS ENUM (
    'PROVISIONAL',
    'CONFIRMED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED',
    'WEATHER_DELAYED'
);

CREATE TYPE public.appointment_type AS ENUM (
    'PREPARATION',
    'COATING',
    'REPAIR',
    'INSPECTION',
    'SINGLE_VISIT'
);

CREATE TYPE public.approval_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'CANCELLED'
);

CREATE TYPE public.approval_type AS ENUM (
    'QUOTATION',
    'CUSTOMER_MESSAGE',
    'BOOKING_CHANGE',
    'DISCOUNT',
    'AD_SPEND',
    'MATERIAL_PURCHASE'
);

CREATE TYPE public.bookkeeping_review_status AS ENUM (
    'PENDING',
    'AUTO_APPLIED',
    'APPROVED',
    'REJECTED',
    'ESCALATED'
);

CREATE TYPE public.briefing_kind AS ENUM (
    'MORNING',
    'EVENING'
);

CREATE TYPE public.campaign_status AS ENUM (
    'DRAFT',
    'PROPOSED',
    'PENDING_APPROVAL',
    'APPROVED',
    'LIVE_SIMULATED',
    'LIVE',
    'PAUSED',
    'ENDED'
);

CREATE TYPE public.commercial_pipeline_stage AS ENUM (
    'DISCOVERED',
    'RESEARCH_REQUIRED',
    'QUALIFIED',
    'CONTACT_VERIFIED',
    'OUTREACH_DRAFTED',
    'APPROVED',
    'CONTACTED',
    'REPLIED',
    'SITE_SURVEY_REQUESTED',
    'QUOTATION_SUBMITTED',
    'NEGOTIATION',
    'WON',
    'LOST',
    'DO_NOT_CONTACT'
);

CREATE TYPE public.compliance_status AS ENUM (
    'NOT_APPLICABLE',
    'INFO_REQUIRED',
    'UPCOMING',
    'PREPARATION_REQUIRED',
    'AWAITING_APPROVAL',
    'SUBMITTED',
    'ACCEPTED',
    'PAYMENT_REQUIRED',
    'COMPLETED',
    'OVERDUE'
);

CREATE TYPE public.content_platform AS ENUM (
    'FACEBOOK',
    'INSTAGRAM',
    'TIKTOK',
    'GOOGLE_BUSINESS',
    'WEBSITE'
);

CREATE TYPE public.content_status AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'SCHEDULED',
    'PUBLISHED',
    'FAILED',
    'REJECTED'
);

CREATE TYPE public.delivery_channel AS ENUM (
    'DASHBOARD',
    'TELEGRAM',
    'EMAIL'
);

CREATE TYPE public.directors_loan_entry_kind AS ENUM (
    'WITHDRAWAL',
    'INTRODUCTION',
    'REPAYMENT',
    'ADJUSTMENT'
);

CREATE TYPE public.dividend_proposal_status AS ENUM (
    'DRAFT',
    'AWAITING_APPROVAL',
    'APPROVED',
    'REJECTED',
    'PAID'
);

CREATE TYPE public.drying_status AS ENUM (
    'NOT_APPLICABLE',
    'AWAITING_DRY',
    'SURFACE_DRY',
    'INSUFFICIENT',
    'CONFIRMED_ON_SITE'
);

CREATE TYPE public.expense_category AS ENUM (
    'MATERIALS',
    'FUEL',
    'ADVERTISING',
    'EQUIPMENT',
    'INSURANCE',
    'PROFESSIONAL',
    'OTHER'
);

CREATE TYPE public.experiment_status AS ENUM (
    'DRAFT',
    'RUNNING',
    'COMPLETED',
    'STOPPED'
);

CREATE TYPE public.finance_sync_kind AS ENUM (
    'FREEAGENT_INVOICES',
    'FREEAGENT_BANK',
    'FREEAGENT_CONTACTS',
    'FREEAGENT_BILLS',
    'FREEAGENT_FULL'
);

CREATE TYPE public.finance_sync_status AS ENUM (
    'RUNNING',
    'SUCCEEDED',
    'PARTIAL',
    'FAILED',
    'SKIPPED'
);

CREATE TYPE public.flyer_campaign_status AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'ORDER_PACK_READY',
    'DISTRIBUTED',
    'CANCELLED'
);

CREATE TYPE public.freeagent_state AS ENUM (
    'NOT_CONFIGURED',
    'PENDING_OAUTH',
    'CONNECTED',
    'ERROR'
);

CREATE TYPE public.growth_fund_entry_type AS ENUM (
    'OPENING_BALANCE',
    'REVENUE_ALLOCATION',
    'AD_EXPENDITURE',
    'COMMITTED_BUDGET',
    'REFUND_ADJUSTMENT',
    'MANUAL_CONTRIBUTION',
    'REVERSAL',
    'TRANSFER_RECOMMENDATION'
);

CREATE TYPE public.integration_state AS ENUM (
    'NOT_CONFIGURED',
    'SANDBOX',
    'CONNECTED',
    'ERROR'
);

CREATE TYPE public.invoice_status AS ENUM (
    'DRAFT',
    'SENT',
    'PART_PAID',
    'PAID',
    'OVERDUE',
    'VOID'
);

CREATE TYPE public.job_run_status AS ENUM (
    'PENDING',
    'RUNNING',
    'SUCCEEDED',
    'FAILED',
    'SKIPPED'
);

CREATE TYPE public.job_status AS ENUM (
    'DRAFT',
    'AWAITING_PREP_BOOKING',
    'BOOKED',
    'PREPARATION_SCHEDULED',
    'PREPARATION_COMPLETED',
    'RESTORATION_PENDING',
    'COATING_SCHEDULED',
    'COATING_COMPLETED',
    'COMPLETED',
    'CANCELLED',
    'ON_HOLD'
);

CREATE TYPE public.legal_structure AS ENUM (
    'UK_PRIVATE_LIMITED'
);

CREATE TYPE public.marketing_director_mode AS ENUM (
    'OBSERVATION',
    'RECOMMEND',
    'CONTROLLED_AUTO'
);

CREATE TYPE public.message_category AS ENUM (
    'TRANSACTIONAL',
    'PROMOTIONAL'
);

CREATE TYPE public.message_channel AS ENUM (
    'EMAIL',
    'SMS',
    'WHATSAPP',
    'PORTAL'
);

CREATE TYPE public.notification_priority AS ENUM (
    'LOW',
    'NORMAL',
    'HIGH',
    'URGENT'
);

CREATE TYPE public.onboarding_task_status AS ENUM (
    'NOT_APPLICABLE',
    'INFO_REQUIRED',
    'UPCOMING',
    'PREPARATION_REQUIRED',
    'AWAITING_APPROVAL',
    'SUBMITTED',
    'COMPLETED',
    'OVERDUE'
);

CREATE TYPE public.operating_mode AS ENUM (
    'MANUAL',
    'SUPERVISED',
    'CONTROLLED'
);

CREATE TYPE public.organic_platform AS ENUM (
    'FACEBOOK',
    'INSTAGRAM'
);

CREATE TYPE public.outbound_status AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'QUEUED',
    'SENT',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE public.outbox_status AS ENUM (
    'PENDING',
    'SENDING',
    'DELIVERED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE public.outreach_message_status AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'SENT',
    'REPLIED',
    'SUPPRESSED',
    'FAILED'
);

CREATE TYPE public.outreach_status AS ENUM (
    'NEW',
    'RESEARCHED',
    'READY_TO_CONTACT',
    'CONTACTED',
    'REPLIED',
    'NOT_SUITABLE',
    'SUPPRESSED'
);

CREATE TYPE public.payroll_status AS ENUM (
    'UNKNOWN',
    'NOT_REGISTERED',
    'REGISTERED'
);

CREATE TYPE public.pipeline_stage AS ENUM (
    'NEW_ENQUIRY',
    'AWAITING_INFORMATION',
    'AWAITING_PHOTOGRAPHS',
    'QUOTE_GENERATED',
    'QUOTE_SENT',
    'QUOTE_ACCEPTED',
    'REGIONAL_WAITING_LIST',
    'BOOKING_PENDING',
    'BOOKED',
    'WASHING_COMPLETED',
    'RESTORATION_PENDING',
    'JOB_COMPLETED',
    'INVOICED',
    'PAID',
    'REVIEW_REQUESTED',
    'REPEAT_CUSTOMER',
    'CANCELLED_OR_LOST'
);

CREATE TYPE public.pricing_rule_type AS ENUM (
    'PER_SQM',
    'MINIMUM_JOB',
    'WASHING_SURCHARGE',
    'COATING_SURCHARGE',
    'REPAIR_UNIT',
    'TRAVEL',
    'COMMERCIAL_MULTIPLIER',
    'CONDITION_SURCHARGE',
    'VAT_RATE',
    'MIN_CONTRIBUTION_MARGIN'
);

CREATE TYPE public.quotation_status AS ENUM (
    'DRAFT',
    'PROVISIONAL',
    'PENDING_APPROVAL',
    'SENT',
    'ACCEPTED',
    'REJECTED',
    'EXPIRED'
);

CREATE TYPE public.service_category AS ENUM (
    'RESTORATION',
    'CLEANING',
    'REPAIR',
    'COMMERCIAL'
);

CREATE TYPE public.stock_category AS ENUM (
    'COATING',
    'CHEMICAL',
    'SEALANT',
    'REPAIR',
    'CONSUMABLE',
    'PPE',
    'EQUIPMENT'
);

CREATE TYPE public.surface_condition AS ENUM (
    'GOOD',
    'FAIR',
    'POOR',
    'HEAVILY_DEGRADED'
);

CREATE TYPE public.surface_type AS ENUM (
    'TARMAC',
    'BLOCK_PAVING',
    'IMPRINTED_CONCRETE',
    'CONCRETE',
    'OTHER'
);

CREATE TYPE public.sync_source AS ENUM (
    'MANUAL',
    'CSV',
    'FREEAGENT'
);

CREATE TYPE public.user_role AS ENUM (
    'OWNER',
    'ADMIN',
    'ACCOUNTANT',
    'STAFF'
);

CREATE TYPE public.vat_status AS ENUM (
    'UNKNOWN',
    'NOT_REGISTERED',
    'REGISTERED',
    'APPLIED'
);

CREATE TYPE public.work_activity AS ENUM (
    'WASHING',
    'COATING',
    'REPAIR'
);

CREATE TABLE public.agent_action_permissions (
    id uuid NOT NULL,
    agent_slug character varying(60) NOT NULL,
    action_key character varying(80) NOT NULL,
    allowed_in_controlled boolean NOT NULL,
    requires_approval boolean NOT NULL,
    daily_limit integer
);

CREATE TABLE public.agent_profiles (
    id uuid NOT NULL,
    slug character varying(60) NOT NULL,
    name character varying(120) NOT NULL,
    operating_mode public.operating_mode NOT NULL,
    is_paused boolean NOT NULL,
    emergency_stop boolean NOT NULL,
    config_json text NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.agent_tasks (
    id uuid NOT NULL,
    agent_slug character varying(60) NOT NULL,
    assigned_by character varying(60) NOT NULL,
    status public.agent_task_status NOT NULL,
    priority integer NOT NULL,
    action_key character varying(80) NOT NULL,
    title character varying(255) NOT NULL,
    payload_json text NOT NULL,
    result_json text,
    iteration_count integer NOT NULL,
    max_iterations integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone
);

CREATE TABLE public.ai_usage_events (
    id uuid NOT NULL,
    provider character varying(40) NOT NULL,
    model character varying(80) NOT NULL,
    agent_slug character varying(60) NOT NULL,
    prompt_tokens integer NOT NULL,
    completion_tokens integer NOT NULL,
    estimated_cost_gbp numeric(10,4) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.appointment_weather_checks (
    id uuid NOT NULL,
    appointment_id uuid NOT NULL,
    activity public.work_activity NOT NULL,
    suitability_score integer NOT NULL,
    is_safe boolean NOT NULL,
    requires_on_site_confirmation boolean NOT NULL,
    detail_json text NOT NULL,
    checked_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.appointments (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    appointment_type public.appointment_type NOT NULL,
    status public.appointment_status NOT NULL,
    scheduled_start timestamp with time zone NOT NULL,
    scheduled_end timestamp with time zone NOT NULL,
    duration_minutes integer NOT NULL,
    latitude double precision,
    longitude double precision,
    postcode character varying(12),
    travel_minutes_estimate integer,
    weather_suitable boolean,
    weather_notes text,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.approval_requests (
    id uuid NOT NULL,
    approval_type public.approval_type NOT NULL,
    status public.approval_status NOT NULL,
    title character varying(255) NOT NULL,
    summary text,
    entity_type character varying(60),
    entity_id uuid,
    requested_by character varying(60) NOT NULL,
    decided_by_user_id uuid,
    decision_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    decided_at timestamp with time zone
);

CREATE TABLE public.assistant_conversations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.assistant_messages (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    tool_calls_json text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.attribution_events (
    id uuid NOT NULL,
    customer_id uuid,
    enquiry_id uuid,
    quotation_id uuid,
    campaign_id uuid,
    flyer_campaign_id uuid,
    source character varying(80) NOT NULL,
    medium character varying(80) NOT NULL,
    content character varying(120),
    utm_campaign character varying(120),
    utm_source character varying(80),
    utm_medium character varying(80),
    utm_content character varying(120),
    utm_term character varying(120),
    landed_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.audit_events (
    id uuid NOT NULL,
    actor_type character varying(40) NOT NULL,
    actor_id character varying(120),
    action character varying(120) NOT NULL,
    entity_type character varying(60),
    entity_id character varying(64),
    detail_json text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.background_job_runs (
    id uuid NOT NULL,
    task_name character varying(80) NOT NULL,
    dedupe_key character varying(120),
    status public.job_run_status NOT NULL,
    worker_id character varying(120),
    detail_json text NOT NULL,
    error_message text,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.bank_transactions (
    id uuid NOT NULL,
    external_id character varying(120),
    freeagent_url character varying(255),
    freeagent_explanation_url character varying(255),
    description character varying(255) NOT NULL,
    amount_gbp numeric(12,2) NOT NULL,
    transacted_at date NOT NULL,
    source public.sync_source NOT NULL,
    matched_invoice_id uuid,
    matched_expense_id uuid,
    suggested_category public.expense_category,
    categorisation_confidence integer,
    review_item_id uuid,
    is_duplicate boolean NOT NULL,
    is_reconciled boolean NOT NULL,
    imported_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.bookkeeping_review_items (
    id uuid NOT NULL,
    bank_transaction_id uuid,
    receipt_id uuid,
    suggested_category public.expense_category,
    confidence_score integer NOT NULL,
    plain_explanation text NOT NULL,
    status public.bookkeeping_review_status NOT NULL,
    is_personal_expenditure boolean NOT NULL,
    receipt_required boolean NOT NULL,
    vat_likely boolean NOT NULL,
    possible_duplicate boolean NOT NULL,
    matched_invoice_id uuid,
    context_json jsonb,
    resolved_at timestamp with time zone,
    resolved_by character varying(80),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.briefing_records (
    id uuid NOT NULL,
    kind public.briefing_kind NOT NULL,
    content_json text NOT NULL,
    generated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.commercial_leads (
    id uuid NOT NULL,
    business_name character varying(255) NOT NULL,
    address_line1 character varying(255),
    town character varying(120),
    postcode character varying(12),
    territory_id uuid,
    website character varying(255),
    category character varying(120),
    contact_email character varying(320),
    contact_phone character varying(40),
    lead_source character varying(80) NOT NULL,
    outreach_status public.outreach_status NOT NULL,
    score integer NOT NULL,
    is_corporate_subscriber boolean,
    opt_out boolean NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.commercial_prospects (
    id uuid NOT NULL,
    dedupe_key character varying(64) NOT NULL,
    business_name character varying(255) NOT NULL,
    business_type character varying(120),
    site_address text,
    postcode character varying(12),
    territory_id uuid,
    website character varying(255),
    contact_name character varying(200),
    contact_email character varying(320),
    contact_phone character varying(40),
    source_name character varying(120) NOT NULL,
    source_url character varying(500),
    verified_on date,
    confidence integer NOT NULL,
    opportunity_category character varying(120),
    lead_score integer NOT NULL,
    outreach_status public.outreach_status NOT NULL,
    lawful_basis character varying(80),
    is_corporate_subscriber boolean,
    opt_out boolean NOT NULL,
    evidence_json jsonb,
    google_place_id character varying(120),
    registered_address text,
    trading_premises_note text,
    responsible_org_hint character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.company_onboarding_tasks (
    id uuid NOT NULL,
    slug character varying(80) NOT NULL,
    title character varying(200) NOT NULL,
    plain_language text NOT NULL,
    status public.onboarding_task_status NOT NULL,
    due_date date,
    evidence_note text,
    sort_order integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.company_profiles (
    id uuid NOT NULL,
    legal_structure public.legal_structure NOT NULL,
    registered_name character varying(200),
    companies_house_number character varying(16),
    incorporation_date date,
    trading_start_date date,
    registered_office text,
    accounting_reference_month integer,
    accounting_reference_day integer,
    company_utr character varying(20),
    vat_status public.vat_status NOT NULL,
    vat_number character varying(20),
    paye_status public.payroll_status NOT NULL,
    paye_reference character varying(32),
    corporation_tax_registered boolean,
    accountant_name character varying(200),
    accountant_email character varying(320),
    shareholders_json jsonb,
    directors_json jsonb,
    director_desired_monthly_net_gbp numeric(12,2),
    mettle_account_hint character varying(255),
    freeagent_configured boolean NOT NULL,
    onboarding_completed_at timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.competitor_intelligence_findings (
    id uuid NOT NULL,
    competitor_name character varying(255) NOT NULL,
    territory_code character varying(10),
    category character varying(80),
    finding_type character varying(80) NOT NULL,
    summary text NOT NULL,
    source_name character varying(120) NOT NULL,
    source_url character varying(500),
    confidence integer NOT NULL,
    retrieved_at timestamp with time zone DEFAULT now() NOT NULL,
    payload_json jsonb
);

CREATE TABLE public.compliance_obligations (
    id uuid NOT NULL,
    slug character varying(80) NOT NULL,
    title character varying(200) NOT NULL,
    plain_language text NOT NULL,
    why_it_matters text NOT NULL,
    source_url character varying(500),
    rule_version character varying(40),
    due_date date,
    status public.compliance_status NOT NULL,
    evidence_note text,
    sort_order integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.customer_properties (
    id uuid NOT NULL,
    customer_id uuid NOT NULL,
    address_line1 character varying(255) NOT NULL,
    address_line2 character varying(255),
    town character varying(120) NOT NULL,
    postcode character varying(12) NOT NULL,
    territory_id uuid,
    latitude double precision,
    longitude double precision
);

CREATE TABLE public.customers (
    id uuid NOT NULL,
    email character varying(320) NOT NULL,
    phone character varying(40),
    full_name character varying(200) NOT NULL,
    consent_marketing boolean NOT NULL,
    consent_service_messages boolean NOT NULL,
    source character varying(120),
    campaign character varying(120),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.directors_loan_entries (
    id uuid NOT NULL,
    kind public.directors_loan_entry_kind NOT NULL,
    amount_gbp numeric(12,2) NOT NULL,
    transacted_at date NOT NULL,
    note character varying(255) NOT NULL,
    bank_transaction_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.dividend_proposals (
    id uuid NOT NULL,
    amount_gbp numeric(12,2) NOT NULL,
    proposed_payment_date date NOT NULL,
    distributable_profit_at_proposal_gbp numeric(12,2) NOT NULL,
    company_cash_at_proposal_gbp numeric(12,2) NOT NULL,
    lawful boolean NOT NULL,
    status public.dividend_proposal_status NOT NULL,
    board_minutes_text text,
    voucher_text text,
    approved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.enquiries (
    id uuid NOT NULL,
    customer_id uuid NOT NULL,
    stage public.pipeline_stage NOT NULL,
    surface_type public.surface_type,
    message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.equipment_assets (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    next_service_due date,
    is_active boolean NOT NULL
);

CREATE TABLE public.expenses (
    id uuid NOT NULL,
    description character varying(255) NOT NULL,
    category public.expense_category NOT NULL,
    amount_gbp numeric(12,2) NOT NULL,
    vat_gbp numeric(12,2) NOT NULL,
    expense_date date NOT NULL,
    job_id uuid,
    territory_id uuid,
    source public.sync_source NOT NULL,
    receipt_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.finance_sync_runs (
    id uuid NOT NULL,
    kind public.finance_sync_kind NOT NULL,
    status public.finance_sync_status NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    finished_at timestamp with time zone,
    fetched_count integer NOT NULL,
    applied_count integer NOT NULL,
    skipped_duplicates integer NOT NULL,
    detail_json text NOT NULL,
    error_message text,
    dedupe_key character varying(120),
    freeagent_connection_id uuid
);

CREATE TABLE public.financial_report_records (
    id uuid NOT NULL,
    period character varying(16) NOT NULL,
    title character varying(200) NOT NULL,
    payload_json text NOT NULL,
    dashboard_path character varying(120) NOT NULL,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    telegram_sent boolean NOT NULL
);

CREATE TABLE public.flyer_campaigns (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    territory_id uuid,
    postcode_targets text NOT NULL,
    quantity integer NOT NULL,
    print_cost_gbp numeric(12,2) NOT NULL,
    distribution_cost_gbp numeric(12,2) NOT NULL,
    qr_slug character varying(40) NOT NULL,
    landing_path character varying(255) NOT NULL,
    status public.flyer_campaign_status NOT NULL,
    distribution_date date,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.freeagent_connections (
    id uuid NOT NULL,
    state public.freeagent_state NOT NULL,
    last_sync_at timestamp with time zone,
    last_error text,
    organisation_name character varying(200),
    access_token text,
    refresh_token text,
    token_expires_at timestamp with time zone,
    oauth_state character varying(64),
    freeagent_company_url character varying(255)
);

CREATE TABLE public.freeagent_resource_cache (
    id uuid NOT NULL,
    resource_key character varying(120) NOT NULL,
    payload_json text NOT NULL,
    fetched_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.invoice_lines (
    id uuid NOT NULL,
    invoice_id uuid NOT NULL,
    description character varying(255) NOT NULL,
    quantity numeric(10,2) NOT NULL,
    unit_price_gbp numeric(12,2) NOT NULL,
    line_total_gbp numeric(12,2) NOT NULL
);

CREATE TABLE public.invoices (
    id uuid NOT NULL,
    invoice_number character varying(32) NOT NULL,
    customer_id uuid NOT NULL,
    job_id uuid,
    quotation_id uuid,
    status public.invoice_status NOT NULL,
    issue_date date NOT NULL,
    due_date date NOT NULL,
    subtotal_ex_vat_gbp numeric(12,2) NOT NULL,
    vat_gbp numeric(12,2) NOT NULL,
    total_inc_vat_gbp numeric(12,2) NOT NULL,
    amount_paid_gbp numeric(12,2) NOT NULL,
    freeagent_url character varying(255),
    freeagent_id character varying(64),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.jobs (
    id uuid NOT NULL,
    reference character varying(24) NOT NULL,
    customer_id uuid NOT NULL,
    quotation_id uuid,
    property_id uuid,
    territory_id uuid,
    status public.job_status NOT NULL,
    requires_two_stage boolean NOT NULL,
    preparation_completed_at timestamp with time zone,
    coating_completed_at timestamp with time zone,
    seven_day_target_date date,
    drying_status public.drying_status NOT NULL,
    customer_washed_already boolean NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_before_after_packages (
    id uuid NOT NULL,
    job_id uuid,
    before_asset_id uuid,
    after_asset_id uuid,
    layout_status character varying(40) NOT NULL,
    content_item_id uuid,
    customer_permission boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_brand_profiles (
    id uuid NOT NULL,
    business_name character varying(200) NOT NULL,
    primary_colour character varying(20) NOT NULL,
    secondary_colour character varying(20) NOT NULL,
    phone character varying(40),
    website character varying(255) NOT NULL,
    tagline character varying(255),
    logo_storage_key character varying(255),
    services_summary text,
    service_areas_json jsonb,
    fonts_json jsonb,
    tone_of_voice text,
    approved_claims_json jsonb,
    approved_ctas_json jsonb,
    objectives_json jsonb,
    differentiators_json jsonb,
    demographics_json jsonb,
    photo_permission_policy text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_budget_policies (
    id uuid NOT NULL,
    live_paid_spend_approved boolean NOT NULL,
    emergency_pause_all boolean NOT NULL,
    daily_limit_gbp numeric(12,2) NOT NULL,
    weekly_limit_gbp numeric(12,2) NOT NULL,
    monthly_limit_gbp numeric(12,2) NOT NULL,
    meta_daily_limit_gbp numeric(12,2) NOT NULL,
    google_daily_limit_gbp numeric(12,2) NOT NULL,
    max_single_increase_pct numeric(5,2) NOT NULL,
    research_api_daily_limit_gbp numeric(12,2) NOT NULL,
    outreach_email_enabled boolean NOT NULL,
    outreach_daily_cap integer NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_content_items (
    id uuid NOT NULL,
    platform public.content_platform NOT NULL,
    title character varying(255) NOT NULL,
    body_text text NOT NULL,
    status public.content_status NOT NULL,
    scheduled_for timestamp with time zone,
    media_asset_ids jsonb,
    publish_external_id character varying(120),
    publish_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_director_runs (
    id uuid NOT NULL,
    run_type character varying(40) NOT NULL,
    summary text NOT NULL,
    recommendations_json jsonb,
    evidence_json jsonb,
    pre_launch_mode boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_email_suppressions (
    id uuid NOT NULL,
    email_normalized character varying(320) NOT NULL,
    reason character varying(120),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_experiments (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    hypothesis text NOT NULL,
    variant_a text NOT NULL,
    variant_b text NOT NULL,
    status public.experiment_status NOT NULL,
    spend_gbp numeric(12,2) NOT NULL,
    enquiries integer NOT NULL,
    quotations integer NOT NULL,
    bookings integer NOT NULL,
    revenue_gbp numeric(12,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_growth_fund_ledger (
    id uuid NOT NULL,
    entry_type public.growth_fund_entry_type NOT NULL,
    amount_gbp numeric(12,2) NOT NULL,
    eligible_revenue_gbp numeric(12,2),
    allocation_pct numeric(5,2),
    bank_transaction_id uuid,
    invoice_id uuid,
    campaign_id uuid,
    dedupe_key character varying(120) NOT NULL,
    description text,
    metadata_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_growth_fund_settings (
    id uuid NOT NULL,
    enabled boolean NOT NULL,
    allocation_pct numeric(5,2) NOT NULL,
    initial_launch_contribution_gbp numeric(12,2) NOT NULL,
    initial_launch_recorded boolean NOT NULL,
    mettle_pot_status character varying(40) NOT NULL,
    notes text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_integration_secrets (
    id uuid NOT NULL,
    provider character varying(40) NOT NULL,
    encrypted_payload text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_integrations (
    id uuid NOT NULL,
    platform public.ad_platform NOT NULL,
    state public.integration_state NOT NULL,
    last_error text,
    last_sync_at timestamp with time zone,
    config_note text
);

CREATE TABLE public.marketing_job_media_staging (
    id uuid NOT NULL,
    job_id uuid,
    job_reference character varying(24),
    asset_id uuid NOT NULL,
    phase character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_launch_plans (
    id uuid NOT NULL,
    launch_date date,
    plan_json jsonb,
    generated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_media_assets (
    id uuid NOT NULL,
    storage_key character varying(255) NOT NULL,
    filename character varying(255) NOT NULL,
    content_sha256 character varying(64) NOT NULL,
    mime_type character varying(80) NOT NULL,
    job_id uuid,
    source character varying(40) NOT NULL,
    customer_permission boolean NOT NULL,
    is_ai_generated boolean NOT NULL,
    category character varying(40) NOT NULL,
    telegram_file_id character varying(200),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_meta_leads (
    id uuid NOT NULL,
    leadgen_id character varying(120) NOT NULL,
    enquiry_id uuid,
    payload_json jsonb,
    dedupe_key character varying(64) NOT NULL,
    ingested_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_organic_post_snapshots (
    id uuid NOT NULL,
    post_id uuid NOT NULL,
    captured_at timestamp with time zone DEFAULT now() NOT NULL,
    metrics_json jsonb NOT NULL
);

CREATE TABLE public.marketing_organic_posts (
    id uuid NOT NULL,
    platform public.organic_platform NOT NULL,
    external_post_id character varying(120) NOT NULL,
    permalink character varying(500),
    caption text,
    published_at timestamp with time zone,
    media_refs_json jsonb,
    format character varying(40),
    metrics_json jsonb,
    ai_analysis_json jsonb,
    raw_payload_json jsonb,
    last_synced_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_prospect_research_runs (
    id uuid NOT NULL,
    territory_id uuid,
    category character varying(80),
    sources_json jsonb,
    imported_count integer NOT NULL,
    api_cost_estimate_gbp numeric(10,4) NOT NULL,
    status character varying(40) NOT NULL,
    detail_json jsonb,
    ran_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_publication_log (
    id uuid NOT NULL,
    content_item_id uuid NOT NULL,
    platform character varying(40) NOT NULL,
    idempotency_key character varying(64) NOT NULL,
    status character varying(40) NOT NULL,
    external_id character varying(120),
    error text,
    simulated boolean NOT NULL,
    published_at timestamp with time zone
);

CREATE TABLE public.marketing_rendered_creatives (
    id uuid NOT NULL,
    package_id uuid NOT NULL,
    format character varying(40) NOT NULL,
    storage_key character varying(255) NOT NULL,
    width integer NOT NULL,
    height integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.marketing_research_findings (
    id uuid NOT NULL,
    topic character varying(120) NOT NULL,
    category character varying(80) NOT NULL,
    source character varying(200) NOT NULL,
    source_url character varying(500),
    collected_at timestamp with time zone NOT NULL,
    confidence numeric(4,3) NOT NULL,
    summary text NOT NULL,
    payload_json text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.material_usage (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    stock_item_id uuid NOT NULL,
    estimated_quantity numeric(12,3) NOT NULL,
    actual_quantity numeric(12,3),
    recorded_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.message_templates (
    id uuid NOT NULL,
    slug character varying(80) NOT NULL,
    name character varying(160) NOT NULL,
    channel public.message_channel NOT NULL,
    category public.message_category NOT NULL,
    subject_template character varying(255),
    body_template text NOT NULL,
    is_active boolean NOT NULL
);

CREATE TABLE public.notification_deliveries (
    id uuid NOT NULL,
    channel public.delivery_channel NOT NULL,
    title character varying(255) NOT NULL,
    body text NOT NULL,
    status character varying(40) NOT NULL,
    briefing_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.notification_outbox (
    id uuid NOT NULL,
    dedupe_key character varying(160),
    channel character varying(40) NOT NULL,
    priority public.notification_priority NOT NULL,
    category character varying(80) NOT NULL,
    title character varying(255) NOT NULL,
    body text NOT NULL,
    payload_json text NOT NULL,
    status public.outbox_status NOT NULL,
    attempts integer NOT NULL,
    max_attempts integer NOT NULL,
    last_error text,
    scheduled_for timestamp with time zone,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.outbound_messages (
    id uuid NOT NULL,
    customer_id uuid,
    template_slug character varying(80),
    channel public.message_channel NOT NULL,
    category public.message_category NOT NULL,
    status public.outbound_status NOT NULL,
    recipient character varying(320) NOT NULL,
    subject character varying(255),
    body text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    sent_at timestamp with time zone,
    provider_response text
);

CREATE TABLE public.outreach_messages (
    id uuid NOT NULL,
    prospect_id uuid NOT NULL,
    subject character varying(255) NOT NULL,
    body_text text NOT NULL,
    status public.outreach_message_status NOT NULL,
    approved_by character varying(120),
    sent_at timestamp with time zone,
    sequence_step integer NOT NULL,
    provider_message_id character varying(255),
    delivery_status character varying(40) NOT NULL,
    bounced_at timestamp with time zone,
    replied_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.owner_calendar_blocks (
    id uuid NOT NULL,
    title character varying(160) NOT NULL,
    block_start timestamp with time zone NOT NULL,
    block_end timestamp with time zone NOT NULL,
    is_unavailable boolean NOT NULL,
    source character varying(40) NOT NULL
);

CREATE TABLE public.payments (
    id uuid NOT NULL,
    invoice_id uuid,
    amount_gbp numeric(12,2) NOT NULL,
    paid_at timestamp with time zone NOT NULL,
    method character varying(40) NOT NULL,
    reference character varying(120),
    source public.sync_source NOT NULL
);

CREATE TABLE public.postcode_districts (
    id uuid NOT NULL,
    district character varying(8) NOT NULL,
    territory_id uuid NOT NULL
);

CREATE TABLE public.pricing_profiles (
    id uuid NOT NULL,
    name character varying(120) NOT NULL,
    version integer NOT NULL,
    notes text,
    is_active boolean NOT NULL,
    effective_from timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.pricing_rules (
    id uuid NOT NULL,
    profile_id uuid NOT NULL,
    rule_type public.pricing_rule_type NOT NULL,
    service_category public.service_category,
    surface_type public.surface_type,
    amount_gbp numeric(12,4) NOT NULL,
    percentage numeric(8,4),
    is_active boolean NOT NULL
);

CREATE TABLE public.product_profiles (
    id uuid NOT NULL,
    name character varying(120) NOT NULL,
    slug character varying(80) NOT NULL,
    min_application_temp_c numeric(5,2) NOT NULL,
    max_application_temp_c numeric(5,2) NOT NULL,
    min_drying_hours integer NOT NULL,
    rain_free_window_hours integer NOT NULL,
    max_wind_mph integer NOT NULL,
    documentation_note text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.quotation_calculations (
    id uuid NOT NULL,
    quotation_id uuid NOT NULL,
    version integer NOT NULL,
    breakdown_json text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.quotation_sections (
    id uuid NOT NULL,
    quotation_id uuid NOT NULL,
    label character varying(120) NOT NULL,
    length_m numeric(8,2),
    width_m numeric(8,2),
    area_sqm numeric(12,2) NOT NULL
);

CREATE TABLE public.quotation_submission_idempotency (
    idempotency_key character varying(64) NOT NULL,
    quotation_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.quotations (
    id uuid NOT NULL,
    reference character varying(20) NOT NULL,
    customer_id uuid NOT NULL,
    enquiry_id uuid,
    service_id uuid,
    territory_id uuid,
    status public.quotation_status NOT NULL,
    surface_type public.surface_type NOT NULL,
    surface_condition public.surface_condition NOT NULL,
    requires_washing boolean NOT NULL,
    customer_washed_already boolean NOT NULL,
    total_area_sqm numeric(12,2) NOT NULL,
    pricing_profile_id uuid,
    subtotal_ex_vat_gbp numeric(12,2) NOT NULL,
    vat_gbp numeric(12,2) NOT NULL,
    total_inc_vat_gbp numeric(12,2) NOT NULL,
    estimated_labour_hours numeric(8,2) NOT NULL,
    estimated_materials_gbp numeric(12,2) NOT NULL,
    estimated_travel_gbp numeric(12,2) NOT NULL,
    estimated_contribution_gbp numeric(12,2) NOT NULL,
    meets_minimum_margin boolean NOT NULL,
    requires_approval boolean NOT NULL,
    provisional_disclaimer text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.receipts (
    id uuid NOT NULL,
    filename character varying(255) NOT NULL,
    storage_key character varying(255),
    content_sha256 character varying(64),
    telegram_file_id character varying(128),
    extracted_merchant character varying(200),
    extracted_total_gbp numeric(12,2),
    extracted_net_gbp numeric(12,2),
    extracted_vat_gbp numeric(12,2),
    extracted_vat_number character varying(32),
    extracted_date date,
    payment_method character varying(80),
    matched_bank_transaction_id uuid,
    processing_status character varying(40) NOT NULL,
    ocr_status character varying(40) NOT NULL,
    raw_extraction_json text,
    freeagent_attach_status character varying(40),
    freeagent_attach_error text,
    freeagent_expense_url character varying(255),
    accounting_route character varying(40),
    uploaded_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.regional_campaigns (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    platform public.ad_platform NOT NULL,
    territory_id uuid,
    service_slug character varying(80),
    status public.campaign_status NOT NULL,
    simulation_only boolean NOT NULL,
    daily_budget_gbp numeric(12,2) NOT NULL,
    monthly_budget_gbp numeric(12,2) NOT NULL,
    spent_gbp numeric(12,2) NOT NULL,
    headline character varying(255),
    body_text text,
    landing_path character varying(255),
    external_campaign_id character varying(120),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.regional_working_days (
    id uuid NOT NULL,
    territory_id uuid NOT NULL,
    work_date date NOT NULL,
    focus character varying(120),
    notes character varying(255)
);

CREATE TABLE public.scheduling_settings (
    id uuid NOT NULL,
    base_latitude numeric(10,7) NOT NULL,
    base_longitude numeric(10,7) NOT NULL,
    base_label character varying(120) NOT NULL,
    max_daily_driving_minutes integer NOT NULL,
    max_job_distance_km numeric(8,2) NOT NULL,
    max_daily_working_hours numeric(4,2) NOT NULL,
    travel_buffer_minutes integer NOT NULL,
    default_prep_duration_minutes integer NOT NULL,
    default_coat_duration_minutes integer NOT NULL,
    min_drying_hours integer NOT NULL,
    seven_day_coating_target_days integer NOT NULL,
    work_day_start time without time zone NOT NULL,
    work_day_end time without time zone NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.services (
    id uuid NOT NULL,
    slug character varying(80) NOT NULL,
    name character varying(160) NOT NULL,
    description text,
    category public.service_category NOT NULL,
    surface_types character varying(255) NOT NULL,
    requires_washing boolean NOT NULL,
    requires_coating boolean NOT NULL,
    is_commercial boolean NOT NULL,
    is_active boolean NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.stock_items (
    id uuid NOT NULL,
    sku character varying(40) NOT NULL,
    name character varying(200) NOT NULL,
    category public.stock_category NOT NULL,
    unit character varying(20) NOT NULL,
    quantity_on_hand numeric(12,3) NOT NULL,
    reorder_level numeric(12,3) NOT NULL,
    coverage_sqm_per_unit numeric(10,3),
    wastage_allowance_pct numeric(5,2) NOT NULL,
    last_purchase_price_gbp numeric(12,2),
    supplier_id uuid,
    is_active boolean NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.suppliers (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    email character varying(320),
    phone character varying(40),
    is_active boolean NOT NULL
);

CREATE TABLE public.tax_reserve_snapshots (
    id uuid NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    rule_version character varying(40) NOT NULL,
    corporation_tax_gbp character varying(32) NOT NULL,
    vat_provision_gbp character varying(32) NOT NULL,
    paye_provision_gbp character varying(32) NOT NULL,
    recommended_total_gbp character varying(32) NOT NULL,
    assumptions_json text NOT NULL,
    data_freshness_note text NOT NULL,
    is_provisional boolean NOT NULL
);

CREATE TABLE public.tax_year_settings (
    id uuid NOT NULL,
    tax_year_label character varying(12) NOT NULL,
    personal_allowance_gbp numeric(12,2) NOT NULL,
    basic_rate_pct numeric(5,2) NOT NULL,
    vat_registration_threshold_gbp numeric(12,2) NOT NULL,
    notes text
);

CREATE TABLE public.telegram_conversation_messages (
    id uuid NOT NULL,
    chat_id integer NOT NULL,
    direction character varying(12) NOT NULL,
    body text NOT NULL,
    telegram_message_id integer,
    outbox_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.telegram_processed_updates (
    id uuid NOT NULL,
    update_id integer NOT NULL,
    chat_id integer,
    message_text text,
    processed_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.territories (
    id uuid NOT NULL,
    code character varying(10) NOT NULL,
    name character varying(120) NOT NULL,
    description text,
    minimum_job_value_gbp numeric(12,2) NOT NULL,
    travel_cost_per_km_gbp numeric(8,4) NOT NULL,
    base_travel_charge_gbp numeric(12,2) NOT NULL,
    marketing_budget_monthly_gbp numeric(12,2),
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.territory_intelligence_scores (
    id uuid NOT NULL,
    territory_id uuid NOT NULL,
    opportunity_score integer NOT NULL,
    demand_indicator integer NOT NULL,
    competition_indicator integer NOT NULL,
    recommended_action text,
    evidence_json jsonb,
    computed_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.territory_localities (
    id uuid NOT NULL,
    territory_id uuid NOT NULL,
    name character varying(120) NOT NULL
);

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(320) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(200) NOT NULL,
    role public.user_role NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.weather_forecast_hours (
    id uuid NOT NULL,
    latitude numeric(10,7) NOT NULL,
    longitude numeric(10,7) NOT NULL,
    forecast_time timestamp with time zone NOT NULL,
    temp_c numeric(5,2) NOT NULL,
    precipitation_mm numeric(6,2) NOT NULL,
    precip_probability_pct integer NOT NULL,
    wind_mph integer NOT NULL,
    humidity_pct integer NOT NULL,
    source character varying(40) NOT NULL,
    fetched_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.agent_action_permissions
    ADD CONSTRAINT agent_action_permissions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.agent_profiles
    ADD CONSTRAINT agent_profiles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.agent_tasks
    ADD CONSTRAINT agent_tasks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.ai_usage_events
    ADD CONSTRAINT ai_usage_events_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.appointment_weather_checks
    ADD CONSTRAINT appointment_weather_checks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.approval_requests
    ADD CONSTRAINT approval_requests_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.assistant_conversations
    ADD CONSTRAINT assistant_conversations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.assistant_messages
    ADD CONSTRAINT assistant_messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.attribution_events
    ADD CONSTRAINT attribution_events_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.background_job_runs
    ADD CONSTRAINT background_job_runs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.bank_transactions
    ADD CONSTRAINT bank_transactions_external_id_key UNIQUE (external_id);

ALTER TABLE ONLY public.bank_transactions
    ADD CONSTRAINT bank_transactions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.bookkeeping_review_items
    ADD CONSTRAINT bookkeeping_review_items_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.briefing_records
    ADD CONSTRAINT briefing_records_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.commercial_leads
    ADD CONSTRAINT commercial_leads_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.commercial_prospects
    ADD CONSTRAINT commercial_prospects_google_place_id_key UNIQUE (google_place_id);

ALTER TABLE ONLY public.commercial_prospects
    ADD CONSTRAINT commercial_prospects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.company_onboarding_tasks
    ADD CONSTRAINT company_onboarding_tasks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.company_profiles
    ADD CONSTRAINT company_profiles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.competitor_intelligence_findings
    ADD CONSTRAINT competitor_intelligence_findings_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.compliance_obligations
    ADD CONSTRAINT compliance_obligations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.customer_properties
    ADD CONSTRAINT customer_properties_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.directors_loan_entries
    ADD CONSTRAINT directors_loan_entries_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.dividend_proposals
    ADD CONSTRAINT dividend_proposals_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.enquiries
    ADD CONSTRAINT enquiries_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.equipment_assets
    ADD CONSTRAINT equipment_assets_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.finance_sync_runs
    ADD CONSTRAINT finance_sync_runs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.financial_report_records
    ADD CONSTRAINT financial_report_records_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.flyer_campaigns
    ADD CONSTRAINT flyer_campaigns_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.freeagent_connections
    ADD CONSTRAINT freeagent_connections_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.freeagent_resource_cache
    ADD CONSTRAINT freeagent_resource_cache_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.invoice_lines
    ADD CONSTRAINT invoice_lines_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_before_after_packages
    ADD CONSTRAINT marketing_before_after_packages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_brand_profiles
    ADD CONSTRAINT marketing_brand_profiles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_budget_policies
    ADD CONSTRAINT marketing_budget_policies_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_content_items
    ADD CONSTRAINT marketing_content_items_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_director_runs
    ADD CONSTRAINT marketing_director_runs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_email_suppressions
    ADD CONSTRAINT marketing_email_suppressions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_experiments
    ADD CONSTRAINT marketing_experiments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_growth_fund_ledger
    ADD CONSTRAINT marketing_growth_fund_ledger_dedupe_key_key UNIQUE (dedupe_key);

ALTER TABLE ONLY public.marketing_growth_fund_ledger
    ADD CONSTRAINT marketing_growth_fund_ledger_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_growth_fund_settings
    ADD CONSTRAINT marketing_growth_fund_settings_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_integration_secrets
    ADD CONSTRAINT marketing_integration_secrets_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_integration_secrets
    ADD CONSTRAINT marketing_integration_secrets_provider_key UNIQUE (provider);

ALTER TABLE ONLY public.marketing_integrations
    ADD CONSTRAINT marketing_integrations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_integrations
    ADD CONSTRAINT marketing_integrations_platform_key UNIQUE (platform);

ALTER TABLE ONLY public.marketing_job_media_staging
    ADD CONSTRAINT marketing_job_media_staging_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_launch_plans
    ADD CONSTRAINT marketing_launch_plans_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_media_assets
    ADD CONSTRAINT marketing_media_assets_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_meta_leads
    ADD CONSTRAINT marketing_meta_leads_dedupe_key_key UNIQUE (dedupe_key);

ALTER TABLE ONLY public.marketing_meta_leads
    ADD CONSTRAINT marketing_meta_leads_leadgen_id_key UNIQUE (leadgen_id);

ALTER TABLE ONLY public.marketing_meta_leads
    ADD CONSTRAINT marketing_meta_leads_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_organic_post_snapshots
    ADD CONSTRAINT marketing_organic_post_snapshots_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_organic_posts
    ADD CONSTRAINT marketing_organic_posts_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_prospect_research_runs
    ADD CONSTRAINT marketing_prospect_research_runs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_publication_log
    ADD CONSTRAINT marketing_publication_log_idempotency_key_key UNIQUE (idempotency_key);

ALTER TABLE ONLY public.marketing_publication_log
    ADD CONSTRAINT marketing_publication_log_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_rendered_creatives
    ADD CONSTRAINT marketing_rendered_creatives_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.marketing_research_findings
    ADD CONSTRAINT marketing_research_findings_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.material_usage
    ADD CONSTRAINT material_usage_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.message_templates
    ADD CONSTRAINT message_templates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.notification_deliveries
    ADD CONSTRAINT notification_deliveries_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.notification_outbox
    ADD CONSTRAINT notification_outbox_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.outbound_messages
    ADD CONSTRAINT outbound_messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.outreach_messages
    ADD CONSTRAINT outreach_messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.owner_calendar_blocks
    ADD CONSTRAINT owner_calendar_blocks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.postcode_districts
    ADD CONSTRAINT postcode_districts_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.pricing_profiles
    ADD CONSTRAINT pricing_profiles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.pricing_rules
    ADD CONSTRAINT pricing_rules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.product_profiles
    ADD CONSTRAINT product_profiles_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.quotation_calculations
    ADD CONSTRAINT quotation_calculations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.quotation_sections
    ADD CONSTRAINT quotation_sections_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.quotation_submission_idempotency
    ADD CONSTRAINT quotation_submission_idempotency_pkey PRIMARY KEY (idempotency_key);

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.regional_campaigns
    ADD CONSTRAINT regional_campaigns_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.regional_working_days
    ADD CONSTRAINT regional_working_days_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.scheduling_settings
    ADD CONSTRAINT scheduling_settings_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.services
    ADD CONSTRAINT services_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.stock_items
    ADD CONSTRAINT stock_items_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.tax_reserve_snapshots
    ADD CONSTRAINT tax_reserve_snapshots_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.tax_year_settings
    ADD CONSTRAINT tax_year_settings_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.telegram_conversation_messages
    ADD CONSTRAINT telegram_conversation_messages_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.telegram_processed_updates
    ADD CONSTRAINT telegram_processed_updates_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.territories
    ADD CONSTRAINT territories_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.territory_intelligence_scores
    ADD CONSTRAINT territory_intelligence_scores_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.territory_intelligence_scores
    ADD CONSTRAINT territory_intelligence_scores_territory_id_key UNIQUE (territory_id);

ALTER TABLE ONLY public.territory_localities
    ADD CONSTRAINT territory_localities_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.telegram_processed_updates
    ADD CONSTRAINT uq_telegram_update_id UNIQUE (update_id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.weather_forecast_hours
    ADD CONSTRAINT weather_forecast_hours_pkey PRIMARY KEY (id);

CREATE INDEX ix_agent_action_permissions_agent_slug ON public.agent_action_permissions USING btree (agent_slug);

CREATE UNIQUE INDEX ix_agent_profiles_slug ON public.agent_profiles USING btree (slug);

CREATE INDEX ix_agent_tasks_agent_slug ON public.agent_tasks USING btree (agent_slug);

CREATE INDEX ix_assistant_conversations_user_id ON public.assistant_conversations USING btree (user_id);

CREATE INDEX ix_assistant_messages_conversation_id ON public.assistant_messages USING btree (conversation_id);

CREATE INDEX ix_audit_events_action ON public.audit_events USING btree (action);

CREATE INDEX ix_audit_events_created_at ON public.audit_events USING btree (created_at);

CREATE INDEX ix_background_job_runs_dedupe_key ON public.background_job_runs USING btree (dedupe_key);

CREATE INDEX ix_background_job_runs_task_name ON public.background_job_runs USING btree (task_name);

CREATE INDEX ix_bookkeeping_review_items_bank_transaction_id ON public.bookkeeping_review_items USING btree (bank_transaction_id);

CREATE INDEX ix_bookkeeping_review_items_receipt_id ON public.bookkeeping_review_items USING btree (receipt_id);

CREATE INDEX ix_commercial_leads_business_name ON public.commercial_leads USING btree (business_name);

CREATE INDEX ix_commercial_leads_postcode ON public.commercial_leads USING btree (postcode);

CREATE INDEX ix_commercial_prospects_business_name ON public.commercial_prospects USING btree (business_name);

CREATE UNIQUE INDEX ix_commercial_prospects_dedupe_key ON public.commercial_prospects USING btree (dedupe_key);

CREATE INDEX ix_commercial_prospects_postcode ON public.commercial_prospects USING btree (postcode);

CREATE UNIQUE INDEX ix_company_onboarding_tasks_slug ON public.company_onboarding_tasks USING btree (slug);

CREATE INDEX ix_competitor_intelligence_findings_competitor_name ON public.competitor_intelligence_findings USING btree (competitor_name);

CREATE INDEX ix_compliance_obligations_due_date ON public.compliance_obligations USING btree (due_date);

CREATE INDEX ix_compliance_obligations_slug ON public.compliance_obligations USING btree (slug);

CREATE INDEX ix_customer_properties_postcode ON public.customer_properties USING btree (postcode);

CREATE INDEX ix_customers_email ON public.customers USING btree (email);

CREATE INDEX ix_directors_loan_entries_kind ON public.directors_loan_entries USING btree (kind);

CREATE INDEX ix_finance_sync_runs_dedupe_key ON public.finance_sync_runs USING btree (dedupe_key);

CREATE INDEX ix_finance_sync_runs_kind ON public.finance_sync_runs USING btree (kind);

CREATE INDEX ix_finance_sync_runs_status ON public.finance_sync_runs USING btree (status);

CREATE INDEX ix_financial_report_records_period ON public.financial_report_records USING btree (period);

CREATE UNIQUE INDEX ix_flyer_campaigns_qr_slug ON public.flyer_campaigns USING btree (qr_slug);

CREATE UNIQUE INDEX ix_freeagent_resource_cache_resource_key ON public.freeagent_resource_cache USING btree (resource_key);

CREATE UNIQUE INDEX ix_invoices_invoice_number ON public.invoices USING btree (invoice_number);

CREATE UNIQUE INDEX ix_jobs_reference ON public.jobs USING btree (reference);

CREATE UNIQUE INDEX ix_marketing_email_suppressions_email_normalized ON public.marketing_email_suppressions USING btree (email_normalized);

CREATE INDEX ix_marketing_job_media_staging_job_reference ON public.marketing_job_media_staging USING btree (job_reference);

CREATE INDEX ix_marketing_media_assets_content_sha256 ON public.marketing_media_assets USING btree (content_sha256);

CREATE INDEX ix_marketing_research_findings_topic ON public.marketing_research_findings USING btree (topic);

CREATE UNIQUE INDEX ix_message_templates_slug ON public.message_templates USING btree (slug);

CREATE INDEX ix_notification_outbox_category ON public.notification_outbox USING btree (category);

CREATE INDEX ix_notification_outbox_channel ON public.notification_outbox USING btree (channel);

CREATE INDEX ix_notification_outbox_dedupe_key ON public.notification_outbox USING btree (dedupe_key);

CREATE INDEX ix_notification_outbox_status ON public.notification_outbox USING btree (status);

CREATE UNIQUE INDEX ix_postcode_districts_district ON public.postcode_districts USING btree (district);

CREATE UNIQUE INDEX ix_product_profiles_slug ON public.product_profiles USING btree (slug);

CREATE INDEX ix_quotation_submission_idempotency_quotation_id ON public.quotation_submission_idempotency USING btree (quotation_id);

CREATE UNIQUE INDEX ix_quotations_reference ON public.quotations USING btree (reference);

CREATE INDEX ix_receipts_content_sha256 ON public.receipts USING btree (content_sha256);

CREATE UNIQUE INDEX ix_services_slug ON public.services USING btree (slug);

CREATE UNIQUE INDEX ix_stock_items_sku ON public.stock_items USING btree (sku);

CREATE INDEX ix_tax_reserve_snapshots_computed_at ON public.tax_reserve_snapshots USING btree (computed_at);

CREATE INDEX ix_telegram_conversation_messages_chat_id ON public.telegram_conversation_messages USING btree (chat_id);

CREATE INDEX ix_telegram_processed_updates_update_id ON public.telegram_processed_updates USING btree (update_id);

CREATE UNIQUE INDEX ix_territories_code ON public.territories USING btree (code);

CREATE INDEX ix_territory_localities_name ON public.territory_localities USING btree (name);

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);

CREATE INDEX ix_weather_forecast_hours_forecast_time ON public.weather_forecast_hours USING btree (forecast_time);

ALTER TABLE ONLY public.appointment_weather_checks
    ADD CONSTRAINT appointment_weather_checks_appointment_id_fkey FOREIGN KEY (appointment_id) REFERENCES public.appointments(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.approval_requests
    ADD CONSTRAINT approval_requests_decided_by_user_id_fkey FOREIGN KEY (decided_by_user_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.attribution_events
    ADD CONSTRAINT attribution_events_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.regional_campaigns(id);

ALTER TABLE ONLY public.attribution_events
    ADD CONSTRAINT attribution_events_flyer_campaign_id_fkey FOREIGN KEY (flyer_campaign_id) REFERENCES public.flyer_campaigns(id);

ALTER TABLE ONLY public.bookkeeping_review_items
    ADD CONSTRAINT bookkeeping_review_items_bank_transaction_id_fkey FOREIGN KEY (bank_transaction_id) REFERENCES public.bank_transactions(id);

ALTER TABLE ONLY public.bookkeeping_review_items
    ADD CONSTRAINT bookkeeping_review_items_receipt_id_fkey FOREIGN KEY (receipt_id) REFERENCES public.receipts(id);

ALTER TABLE ONLY public.commercial_leads
    ADD CONSTRAINT commercial_leads_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.commercial_prospects
    ADD CONSTRAINT commercial_prospects_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.customer_properties
    ADD CONSTRAINT customer_properties_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.customer_properties
    ADD CONSTRAINT customer_properties_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.enquiries
    ADD CONSTRAINT enquiries_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.finance_sync_runs
    ADD CONSTRAINT finance_sync_runs_freeagent_connection_id_fkey FOREIGN KEY (freeagent_connection_id) REFERENCES public.freeagent_connections(id);

ALTER TABLE ONLY public.flyer_campaigns
    ADD CONSTRAINT flyer_campaigns_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.invoice_lines
    ADD CONSTRAINT invoice_lines_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id);

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.customer_properties(id);

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id);

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.marketing_before_after_packages
    ADD CONSTRAINT marketing_before_after_packages_after_asset_id_fkey FOREIGN KEY (after_asset_id) REFERENCES public.marketing_media_assets(id);

ALTER TABLE ONLY public.marketing_before_after_packages
    ADD CONSTRAINT marketing_before_after_packages_before_asset_id_fkey FOREIGN KEY (before_asset_id) REFERENCES public.marketing_media_assets(id);

ALTER TABLE ONLY public.marketing_before_after_packages
    ADD CONSTRAINT marketing_before_after_packages_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES public.marketing_content_items(id);

ALTER TABLE ONLY public.marketing_growth_fund_ledger
    ADD CONSTRAINT marketing_growth_fund_ledger_bank_transaction_id_fkey FOREIGN KEY (bank_transaction_id) REFERENCES public.bank_transactions(id);

ALTER TABLE ONLY public.marketing_growth_fund_ledger
    ADD CONSTRAINT marketing_growth_fund_ledger_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id);

ALTER TABLE ONLY public.marketing_job_media_staging
    ADD CONSTRAINT marketing_job_media_staging_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.marketing_media_assets(id);

ALTER TABLE ONLY public.marketing_organic_post_snapshots
    ADD CONSTRAINT marketing_organic_post_snapshots_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.marketing_organic_posts(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.marketing_prospect_research_runs
    ADD CONSTRAINT marketing_prospect_research_runs_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.marketing_publication_log
    ADD CONSTRAINT marketing_publication_log_content_item_id_fkey FOREIGN KEY (content_item_id) REFERENCES public.marketing_content_items(id);

ALTER TABLE ONLY public.marketing_rendered_creatives
    ADD CONSTRAINT marketing_rendered_creatives_package_id_fkey FOREIGN KEY (package_id) REFERENCES public.marketing_before_after_packages(id);

ALTER TABLE ONLY public.material_usage
    ADD CONSTRAINT material_usage_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id);

ALTER TABLE ONLY public.material_usage
    ADD CONSTRAINT material_usage_stock_item_id_fkey FOREIGN KEY (stock_item_id) REFERENCES public.stock_items(id);

ALTER TABLE ONLY public.notification_deliveries
    ADD CONSTRAINT notification_deliveries_briefing_id_fkey FOREIGN KEY (briefing_id) REFERENCES public.briefing_records(id);

ALTER TABLE ONLY public.outreach_messages
    ADD CONSTRAINT outreach_messages_prospect_id_fkey FOREIGN KEY (prospect_id) REFERENCES public.commercial_prospects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id);

ALTER TABLE ONLY public.postcode_districts
    ADD CONSTRAINT postcode_districts_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.pricing_rules
    ADD CONSTRAINT pricing_rules_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.pricing_profiles(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.quotation_calculations
    ADD CONSTRAINT quotation_calculations_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.quotation_sections
    ADD CONSTRAINT quotation_sections_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.quotation_submission_idempotency
    ADD CONSTRAINT quotation_submission_idempotency_quotation_id_fkey FOREIGN KEY (quotation_id) REFERENCES public.quotations(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_enquiry_id_fkey FOREIGN KEY (enquiry_id) REFERENCES public.enquiries(id);

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pricing_profile_id_fkey FOREIGN KEY (pricing_profile_id) REFERENCES public.pricing_profiles(id);

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.services(id);

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_matched_bank_transaction_id_fkey FOREIGN KEY (matched_bank_transaction_id) REFERENCES public.bank_transactions(id);

ALTER TABLE ONLY public.regional_campaigns
    ADD CONSTRAINT regional_campaigns_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.regional_working_days
    ADD CONSTRAINT regional_working_days_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.stock_items
    ADD CONSTRAINT stock_items_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id);

ALTER TABLE ONLY public.telegram_conversation_messages
    ADD CONSTRAINT telegram_conversation_messages_outbox_id_fkey FOREIGN KEY (outbox_id) REFERENCES public.notification_outbox(id);

ALTER TABLE ONLY public.territory_intelligence_scores
    ADD CONSTRAINT territory_intelligence_scores_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id);

ALTER TABLE ONLY public.territory_localities
    ADD CONSTRAINT territory_localities_territory_id_fkey FOREIGN KEY (territory_id) REFERENCES public.territories(id) ON DELETE CASCADE;

