#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) Vauxoo (<http://vauxoo.com>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by: Julio Cesar Serna Hernandez(julio@vauxoo.com)
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################
import time
from openerp.osv import fields, osv
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_voucher_tax_sat(osv.Model):
    
    _name = 'account.voucher.tax.sat'
    
    _columns = {
        'name': fields.many2one('res.partner', 'Partner'),
        'period_id': fields.many2one('account.period', 'Period'),
        'aml_ids': fields.many2many('account.move.line', 'voucher_tax_sat_rel',
                                        'voucher_tax_sat_id', 'move_line_id',
                                        'Move Lines'),
        'journal_id':fields.many2one('account.journal', 'Journal'), 
        'move_id': fields.many2one('account.move', 'Journal Entry')
    }
    
    def action_close_tax(self, cr, uid, ids, context=None):
        aml_obj = self.pool.get('account.move.line')
        context = context or {}
        ids= isinstance(ids,(int,long)) and [ids] or ids
        for voucher_tax_sat in self.browse(cr, uid, ids, context=context):
            
                move_id = self.create_move_sat(cr, uid, ids, context=context)
                self.write(cr, uid, ids, {'move_id': move_id})
                
                amount_tax_sat = sum([move_line_tax_sat.credit
                            for move_line_tax_sat in voucher_tax_sat.aml_ids])
                            
                self.create_move_line_sat(cr, uid, voucher_tax_sat,
                                            amount_tax_sat, context=context)
                                        
                move_line_copy = [ aml_obj.copy(cr, uid, move_line_tax.id,
                    {
                        'move_id': move_id,
                        'period_id': voucher_tax_sat.period_id.id,
                        'journal_id': voucher_tax_sat.journal_id.id,
                        'credit': 0.0,
                        'debit': move_line_tax.credit,
                    }) for move_line_tax in voucher_tax_sat.aml_ids ]
                    
        return True
    
    def create_move_line_sat(self, cr, uid, voucher_tax_sat, amount, context=None):
        print voucher_tax_sat,'voucher_tax_sat'
        aml_obj = self.pool.get('account.move.line')
        vals = {
            'move_id': voucher_tax_sat.move_id.id,
            'journal_id': voucher_tax_sat.journal_id.id,
            'date' : fields.datetime.now(),
            'period_id' : voucher_tax_sat.period_id.id,
            'debit' : 0.0,
            'name' : _('Payment with Advance'),
            'partner_id' : voucher_tax_sat.name.id,
            'account_id' : voucher_tax_sat.name.property_account_payable.id,
            'credit' : amount,
        }
        return aml_obj.create(cr, uid, vals, context=context)
    
    def create_move_sat(self, cr, uid, ids, context=None):
        account_move_obj = self.pool.get('account.move')
        context = context or {}
        ids= isinstance(ids,(int,long)) and [ids] or ids
        for move_tax_sat in self.browse(cr, uid, ids, context=context):
            vals_move_tax= account_move_obj.account_move_prepare(cr, uid,
                    move_tax_sat.journal_id.id,
                    ref='Entry SAT', context=context)
        return account_move_obj.create(cr, uid, vals_move_tax, context=context)


class account_tax(osv.Model):
    
    _inherit = 'account.tax'
    
    _columns = {
        'tax_sat_ok': fields.boolean('Create entries IVA to SAT'),
        'tax_sat_id': fields.many2one('account.tax', 'Tax of statement SAT')
    }


class account_voucher(osv.Model):
    
    _inherit = 'account.voucher'
    

    def _preparate_move_line_tax(self, cr, uid, src_account_id, dest_account_id,
                            move_id, type, partner, period, journal, date,
                            company_currency, reference_amount,
                            amount_tax_unround, reference_currency_id,
                            tax_id, tax_name, acc_a, amount_base_tax,#informacion de lineas de impuestos
                            factor=0, context=None):
                            
        res = super(account_voucher,
                        self)._preparate_move_line_tax(cr, uid,
                            src_account_id, dest_account_id,
                            move_id, type, partner, period, journal, date,
                            company_currency, reference_amount,
                            amount_tax_unround, reference_currency_id,
                            tax_id, tax_name, acc_a, amount_base_tax,
                            factor=factor, context=context)
        res and res[1].update({
            'tax_id_secondary': res and res[0].get('tax_id_secondary', False),
            'not_move_diot': True,
        })
        print res,'res'
        return res