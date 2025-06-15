/** @odoo-module **/
import {Component, useState, onWillStart} from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";
import {registry} from '@web/core/registry';


class PreviewTable extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({rows: []});
        onWillStart(() => this._fetchPreview());
        // Re-fetch cada vez que cambian estos campos
        this.props.record.on('change:date_from', this, this._fetchPreview);
        this.props.record.on('change:date_to', this, this._fetchPreview);
        this.props.record.on('change:all_subs', this, this._fetchPreview);
        this.props.record.on('change:account_start', this, this._fetchPreview);
        this.props.record.on('change:account_end', this, this._fetchPreview);
    }

    async _fetchPreview() {
        const {date_from, date_to, all_subs, account_start, account_end} = this.props.renderer.state.data;
        this.state.rows = await this.rpc.query({
            model: 'libro.auxiliar.wizard',
            method: 'get_preview_data',
            args: [[this.props.record.id], {
                date_from,
                date_to,
                all_subs,
                account_start: account_start && account_start.res_id,
                account_end: account_end && account_end.res_id,
            }],
        });
    }
}

PreviewTable.template = 'libro_diario_report.PreviewTable';
registry.category('components').add('PreviewTable', PreviewTable);