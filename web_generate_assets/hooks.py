# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
import os

from odoo import fields, registry

logger = logging.getLogger(__name__)


def active_cron_assets():
    """Plan the next execution of the cron responsible to generate assets."""
    if os.environ.get("RUNNING_ENV") == "dev":
        return
    dbname = os.environ.get("DB_NAME")
    reg = registry(dbname)
    with reg.cursor() as cr:
        cron_module, cron_ref = "web_generate_assets", "cron_generate_assets"
        query = """
           SELECT model, res_id
           FROM ir_model_data
           WHERE module=%s
           AND name=%s;
        """
        args = (cron_module, cron_ref)
        cr.execute(query, args)
        row = cr.fetchone()
        # post_load hook is called before the update of the module so the
        # ir_cron record doesn't exist on first install
        if row:
            model, res_id = row
            if model != "ir.cron":
                return
            query = """
                UPDATE ir_cron
                SET active=true, nextcall=%s, priority=%s
                WHERE id=%s
            """
            nextcall = fields.Datetime.to_string(fields.Datetime.now())
            args = (nextcall, -99, res_id)
            cr.execute(query, args)
            logger.info(
                "Cron '%s.%s' planned for execution at %s",
                cron_module,
                cron_ref,
                nextcall,
            )


def post_load_hook():
    active_cron_assets()
