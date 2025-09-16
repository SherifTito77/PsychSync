--
-- PostgreSQL database dump
--

\restrict CCU8JGGscLs1xRJ1qvPe8ahplhfLaw9l3JpvGTddryijjy8LCzzMSckRYTMh88d

-- Dumped from database version 14.19 (Homebrew)
-- Dumped by pg_dump version 14.19 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: citext; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;


--
-- Name: EXTENSION citext; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION citext IS 'data type for case-insensitive character strings';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO psychsync_user;

--
-- Name: assessments; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.assessments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    score uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.assessments OWNER TO psychsync_user;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    actor_user_id uuid,
    action text NOT NULL,
    entity text NOT NULL,
    entity_id uuid,
    meta jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO psychsync_user;

--
-- Name: frameworks; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.frameworks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.frameworks OWNER TO psychsync_user;

--
-- Name: invitations; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.invitations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    email public.citext NOT NULL,
    token text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    accepted_at timestamp with time zone
);


ALTER TABLE public.invitations OWNER TO psychsync_user;

--
-- Name: org_members; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.org_members (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    org_id uuid NOT NULL,
    role text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.org_members OWNER TO psychsync_user;

--
-- Name: organizations; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.organizations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name public.citext NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.organizations OWNER TO psychsync_user;

--
-- Name: question_options; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.question_options (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    question_id uuid NOT NULL,
    label text NOT NULL,
    value text NOT NULL,
    weight numeric,
    "position" integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.question_options OWNER TO psychsync_user;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    text character varying NOT NULL,
    framework_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.questions OWNER TO psychsync_user;

--
-- Name: responses; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.responses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    assessment_id uuid NOT NULL,
    question_id uuid NOT NULL,
    answer_text character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.responses OWNER TO psychsync_user;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.roles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.roles OWNER TO psychsync_user;

--
-- Name: scores; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.scores (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    assessment_id uuid NOT NULL,
    dimension text NOT NULL,
    value numeric NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.scores OWNER TO psychsync_user;

--
-- Name: team_members; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.team_members (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    team_id uuid NOT NULL,
    role character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.team_members OWNER TO psychsync_user;

--
-- Name: teams; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.teams (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.teams OWNER TO psychsync_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: psychsync_user
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email public.citext NOT NULL,
    password_hash text NOT NULL,
    full_name text,
    avatar_url text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO psychsync_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.alembic_version (version_num) FROM stdin;
3da94cd742b9
\.


--
-- Data for Name: assessments; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.assessments (id, user_id, score, created_at) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.audit_logs (id, org_id, actor_user_id, action, entity, entity_id, meta, created_at) FROM stdin;
\.


--
-- Data for Name: frameworks; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.frameworks (id, name, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: invitations; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.invitations (id, org_id, email, token, expires_at, accepted_at) FROM stdin;
\.


--
-- Data for Name: org_members; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.org_members (id, user_id, org_id, role, created_at) FROM stdin;
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.organizations (id, name, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: question_options; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.question_options (id, question_id, label, value, weight, "position") FROM stdin;
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.questions (id, text, framework_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: responses; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.responses (id, assessment_id, question_id, answer_text, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.roles (id, name, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: scores; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.scores (id, assessment_id, dimension, value, created_at) FROM stdin;
\.


--
-- Data for Name: team_members; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.team_members (id, user_id, team_id, role, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.teams (id, org_id, name, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: psychsync_user
--

COPY public.users (id, email, password_hash, full_name, avatar_url, is_active, created_at, updated_at, deleted_at) FROM stdin;
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: assessments assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: frameworks frameworks_name_key; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.frameworks
    ADD CONSTRAINT frameworks_name_key UNIQUE (name);


--
-- Name: frameworks frameworks_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.frameworks
    ADD CONSTRAINT frameworks_pkey PRIMARY KEY (id);


--
-- Name: invitations invitations_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.invitations
    ADD CONSTRAINT invitations_pkey PRIMARY KEY (id);


--
-- Name: invitations invitations_token_key; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.invitations
    ADD CONSTRAINT invitations_token_key UNIQUE (token);


--
-- Name: org_members org_members_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT org_members_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_name_key; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_name_key UNIQUE (name);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: question_options question_options_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: responses responses_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: scores scores_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: scores uq_score_assessment_dimension; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT uq_score_assessment_dimension UNIQUE (assessment_id, dimension);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: assessments assessments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.assessments
    ADD CONSTRAINT assessments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: invitations invitations_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.invitations
    ADD CONSTRAINT invitations_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: org_members org_members_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT org_members_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id);


--
-- Name: org_members org_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.org_members
    ADD CONSTRAINT org_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: question_options question_options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: questions questions_framework_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_framework_id_fkey FOREIGN KEY (framework_id) REFERENCES public.frameworks(id);


--
-- Name: responses responses_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.assessments(id) ON DELETE CASCADE;


--
-- Name: responses responses_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: scores scores_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.assessments(id) ON DELETE CASCADE;


--
-- Name: team_members team_members_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id);


--
-- Name: team_members team_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: teams teams_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: psychsync_user
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id);


--
-- PostgreSQL database dump complete
--

\unrestrict CCU8JGGscLs1xRJ1qvPe8ahplhfLaw9l3JpvGTddryijjy8LCzzMSckRYTMh88d

