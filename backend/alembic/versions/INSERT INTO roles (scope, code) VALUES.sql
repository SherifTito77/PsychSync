INSERT INTO roles (scope, code) VALUES
('org','owner'),('org','admin'),('org','member'),('org','viewer'),
('team','admin'),('team','member'),('team','viewer')
ON CONFLICT DO NOTHING;

