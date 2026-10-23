CREATE TABLE notas (
    id             SERIAL PRIMARY KEY,
    numero         INTEGER     NOT NULL UNIQUE,
    serie          INTEGER     NOT NULL,
    chave          VARCHAR(44) NOT NULL UNIQUE,
    usuario        VARCHAR(100),
    status         VARCHAR(30) NOT NULL DEFAULT 'GERADA',
    c_stat         VARCHAR(10),
    motivo         VARCHAR(500),
    protocolo      VARCHAR(50),
    xml_assinado   TEXT,
    xml_original   TEXT,
    retorno_xml    TEXT,
    criado_em      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transmitido_em TIMESTAMP
);

CREATE OR REPLACE FUNCTION trigger_set_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notas_updated
    BEFORE UPDATE ON notas
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_atualizado_em();
