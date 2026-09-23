package org.sihsalus.content;

import static org.junit.Assert.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Date;

import org.junit.Test;
import org.openmrs.User;
import org.openmrs.api.db.ClobDatatypeStorage;
import org.openmrs.api.handler.OpenmrsObjectSaveHandler;

/** Verifies the native storage normalization used by the Initializer schema check. */
public class FormSchemaPersistenceTest {
    @Test
    public void coreTrimsOnlyOuterWhitespaceWhenSavingTheShippedSchemas() throws Exception {
        for (String filename : new String[] {"CRED-001-TAMIZAJE DE ANEMIA.json",
                "OBST-002-EMBARAZO ACTUAL.json"}) {
            String source = new String(Files.readAllBytes(Paths.get(System.getProperty("content.root"),
                "configuration/ampathforms", filename)), StandardCharsets.UTF_8);
            ClobDatatypeStorage stored = new ClobDatatypeStorage();
            stored.setValue(source);
            new OpenmrsObjectSaveHandler().handle(stored, new User(1), new Date(), null);
            assertEquals(source.trim(), stored.getValue());
            assertNotEquals("A raw file hash must not be used for this stored schema", source, stored.getValue());
            assertTrue("Internal formatting must remain intact", stored.getValue().contains("\n  "));
        }
    }
}
