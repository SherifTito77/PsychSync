-- Enable extensions
weight NUMERIC, -- optional scoring weight
position INT NOT NULL
);
CREATE INDEX question_options_q_pos_idx ON question_options (question_id, position);


-- assessments (an instance of a user taking a framework)
CREATE TABLE assessments (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
framework_id UUID NOT NULL REFERENCES frameworks(id) ON DELETE RESTRICT,
status TEXT NOT NULL CHECK (status IN ('assigned','in_progress','completed','expired')),
started_at timestamptz,
completed_at timestamptz,
created_at timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX assessments_lookup_idx ON assessments (org_id, team_id, user_id, framework_id);


-- responses
CREATE TABLE responses (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
answer_json JSONB NOT NULL, -- supports multi/likert/text
created_at timestamptz NOT NULL DEFAULT NOW(),
UNIQUE (assessment_id, question_id)
);
CREATE INDEX responses_assessment_idx ON responses (assessment_id);


-- scores (normalized dimension scores)
CREATE TABLE scores (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
dimension TEXT NOT NULL, -- e.g., 'O','C','E','A','N' or 'I/E'
value NUMERIC NOT NULL, -- 0..100 or normalized 0..1
created_at timestamptz NOT NULL DEFAULT NOW(),
UNIQUE (assessment_id, dimension)
);
CREATE INDEX scores_assessment_dim_idx ON scores (assessment_id, dimension);


-- invitations
CREATE TABLE invitations (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
email CITEXT NOT NULL,
token TEXT NOT NULL UNIQUE,
expires_at timestamptz NOT NULL,
accepted_at timestamptz
);
CREATE INDEX invitations_org_email_idx ON invitations (org_id, email);


-- audit_logs
CREATE TABLE audit_logs (
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
action TEXT NOT NULL, -- e.g., 'user.invited','assessment.completed'
entity TEXT NOT NULL, -- table name
entity_id UUID,
meta JSONB,
created_at timestamptz NOT NULL DEFAULT NOW()
);
CREATE INDEX audit_logs_org_time_idx ON audit_logs (org_id, created_at DESC);