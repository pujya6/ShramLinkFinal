CREATE TABLE escrow_records (
	id INTEGER NOT NULL,
	amount INTEGER NOT NULL,
	workers_count INTEGER,
	status VARCHAR(9),
	released_at DATETIME,
	payment_method VARCHAR(20),
	transaction_id VARCHAR(100),
	notes TEXT,
	created_at DATETIME,
	updated_at DATETIME,
	job_id INTEGER NOT NULL,
	manager_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(job_id) REFERENCES jobs (id),
	FOREIGN KEY(manager_id) REFERENCES users (id)
);

CREATE TABLE job_applications (
	id INTEGER NOT NULL,
	status VARCHAR(11),
	applied_at DATETIME,
	reviewed_at DATETIME,
	selected_at DATETIME,
	manager_notes TEXT,
	laborer_id INTEGER NOT NULL,
	job_id INTEGER NOT NULL,
	application_date DATE,
	PRIMARY KEY (id),
	CONSTRAINT unique_laborer_job_application UNIQUE (laborer_id, job_id),
	FOREIGN KEY(laborer_id) REFERENCES users (id),
	FOREIGN KEY(job_id) REFERENCES jobs (id)
);

CREATE TABLE jobs (
	id INTEGER NOT NULL,
	job_code VARCHAR(20) NOT NULL,
	title VARCHAR(100) NOT NULL,
	title_hi VARCHAR(100),
	description TEXT,
	skill VARCHAR(12) NOT NULL,
	wage_per_day INTEGER NOT NULL,
	workers_needed INTEGER,
	workers_hired INTEGER,
	shift_timing VARCHAR(50) NOT NULL,
	location VARCHAR(200) NOT NULL,
	latitude FLOAT,
	longitude FLOAT,
	start_date DATE NOT NULL,
	end_date DATE,
	status VARCHAR(9),
	verified_only BOOLEAN,
	mass_hire_enabled BOOLEAN,
	mass_hire_fee INTEGER,
	platform_fee INTEGER,
	total_escrow INTEGER,
	escrow_paid BOOLEAN,
	created_at DATETIME,
	updated_at DATETIME,
	manager_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(manager_id) REFERENCES users (id)
);

CREATE TABLE mass_hire_assignments (
	id INTEGER NOT NULL,
	assigned_at DATETIME,
	status VARCHAR(20),
	request_id INTEGER NOT NULL,
	laborer_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(request_id) REFERENCES mass_hire_requests (id),
	FOREIGN KEY(laborer_id) REFERENCES users (id)
);

CREATE TABLE mass_hire_requests (
	id INTEGER NOT NULL,
	request_code VARCHAR(20) NOT NULL,
	workers_needed INTEGER NOT NULL,
	workers_assigned INTEGER,
	status VARCHAR(20),
	request_date DATE,
	target_date DATE,
	created_at DATETIME,
	updated_at DATETIME,
	job_id INTEGER NOT NULL,
	manager_id INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (request_code),
	FOREIGN KEY(job_id) REFERENCES jobs (id),
	FOREIGN KEY(manager_id) REFERENCES users (id)
);

CREATE TABLE users (
	id INTEGER NOT NULL,
	email VARCHAR(120) NOT NULL,
	phone VARCHAR(20),
	password_hash VARCHAR(255) NOT NULL,
	role VARCHAR(7) NOT NULL,
	name VARCHAR(100) NOT NULL,
	is_verified BOOLEAN,
	is_active BOOLEAN,
	created_at DATETIME,
	updated_at DATETIME,
	age INTEGER,
	skills TEXT,
	upi_id VARCHAR(100),
	eshram_number VARCHAR(50),
	kyc_status VARCHAR(20),
	kyc_method VARCHAR(20),
	factory_name VARCHAR(200),
	factory_address TEXT,
	gstin VARCHAR(30),
	gst_certificate VARCHAR(200),
	pan_number VARCHAR(20),
	PRIMARY KEY (id)
);

CREATE TABLE verification_requests (
	id INTEGER NOT NULL,
	entity_type VARCHAR(20) NOT NULL,
	entity_name VARCHAR(200) NOT NULL,
	owner_name VARCHAR(100) NOT NULL,
	gstin VARCHAR(30),
	eshram_number VARCHAR(50),
	kyc_method VARCHAR(20),
	skill VARCHAR(50),
	age INTEGER,
	city VARCHAR(100),
	documents TEXT,
	status VARCHAR(20),
	reviewed_by INTEGER,
	reviewed_at DATETIME,
	review_notes TEXT,
	submitted_at DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(reviewed_by) REFERENCES users (id)
);

CREATE TABLE worker_ratings (
	id INTEGER NOT NULL,
	rating INTEGER NOT NULL,
	feedback_tags TEXT,
	comment TEXT,
	created_at DATETIME,
	rater_id INTEGER NOT NULL,
	worker_id INTEGER NOT NULL,
	job_id INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(rater_id) REFERENCES users (id),
	FOREIGN KEY(worker_id) REFERENCES users (id),
	FOREIGN KEY(job_id) REFERENCES jobs (id)
);

CREATE INDEX idx_laborer_date ON job_applications (laborer_id, application_date);

CREATE INDEX ix_escrow_records_status ON escrow_records (status);

CREATE INDEX ix_job_applications_application_date ON job_applications (application_date);

CREATE INDEX ix_job_applications_status ON job_applications (status);

CREATE UNIQUE INDEX ix_jobs_job_code ON jobs (job_code);

CREATE INDEX ix_jobs_status ON jobs (status);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE UNIQUE INDEX ix_users_phone ON users (phone);

CREATE INDEX ix_verification_requests_status ON verification_requests (status);
