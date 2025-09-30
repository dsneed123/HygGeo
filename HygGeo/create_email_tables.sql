-- Create EmailTemplate table
CREATE TABLE IF NOT EXISTS accounts_emailtemplate (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    subject VARCHAR(300) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT NOT NULL,
    category VARCHAR(20) NOT NULL DEFAULT 'other',
    available_merge_fields JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
);

-- Create EmailCampaign table
CREATE TABLE IF NOT EXISTS accounts_emailcampaign (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    recipient_type VARCHAR(20) NOT NULL DEFAULT 'all_users',
    mode VARCHAR(10) NOT NULL DEFAULT 'test',
    scheduled_send TIMESTAMP WITH TIME ZONE,
    status VARCHAR(10) NOT NULL DEFAULT 'draft',
    total_recipients INTEGER NOT NULL DEFAULT 0,
    emails_sent INTEGER NOT NULL DEFAULT 0,
    emails_failed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    template_id BIGINT NOT NULL REFERENCES accounts_emailtemplate(id) ON DELETE CASCADE
);

-- Create EmailCampaign custom recipients many-to-many table
CREATE TABLE IF NOT EXISTS accounts_emailcampaign_custom_recipients (
    id BIGSERIAL PRIMARY KEY,
    emailcampaign_id BIGINT NOT NULL REFERENCES accounts_emailcampaign(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE(emailcampaign_id, user_id)
);

-- Create EmailLog table
CREATE TABLE IF NOT EXISTS accounts_emaillog (
    id BIGSERIAL PRIMARY KEY,
    status VARCHAR(10) NOT NULL DEFAULT 'pending',
    subject_sent VARCHAR(300) NOT NULL,
    error_message TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    campaign_id BIGINT NOT NULL REFERENCES accounts_emailcampaign(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE(campaign_id, recipient_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS accounts_emailtemplate_created_by_id_idx ON accounts_emailtemplate(created_by_id);
CREATE INDEX IF NOT EXISTS accounts_emailcampaign_template_id_idx ON accounts_emailcampaign(template_id);
CREATE INDEX IF NOT EXISTS accounts_emailcampaign_created_by_id_idx ON accounts_emailcampaign(created_by_id);
CREATE INDEX IF NOT EXISTS accounts_emaillog_campaign_id_idx ON accounts_emaillog(campaign_id);
CREATE INDEX IF NOT EXISTS accounts_emaillog_recipient_id_idx ON accounts_emaillog(recipient_id);