/** @odoo-module **/
import { registry } from '@web/core/registry';
import { useState } from '@odoo/owl';
import { FormController } from '@web/views/form/form_controller';

class LibroAuxiliarWizardController extends FormController {
    setup() {
        super.setup();
        // Estado reactivo: controla mostrar/ocultar account_end
        this.state = useState({ allSubs: this.props.renderer.state.data.all_subs });
        // Cuando el usuario cambie all_subs en el servidor, lo sincronizamos
        this.renderer.onFieldChange('all_subs', value => {
            this.state.allSubs = value;
        });
    }
}

// Registrar el controlador para forms con js_class "LibroAuxiliarWizard"
registry.category('controllers').add('libro_auxiliar_wizard', {
    Component: LibroAuxiliarWizardController,
    priority: 10,
});