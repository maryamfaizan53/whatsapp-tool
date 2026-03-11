"""
Widget Configuration Service for WhatsApp RAG Assistant
"""
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..models.widget_config import WidgetConfiguration
from ..models.business import Business


class WidgetService:
    def __init__(self):
        pass

    def get_widget_configuration(
        self,
        business_id: str,
        db: Session
    ) -> WidgetConfiguration:
        """
        Get the widget configuration for a business
        """
        widget_config = db.query(WidgetConfiguration).filter(
            WidgetConfiguration.business_id == business_id
        ).first()

        # If no configuration exists, create a default one
        if not widget_config:
            widget_config = WidgetConfiguration(
                business_id=business_id,
                position="bottom-right",
                color_scheme="#25D366",  # WhatsApp green
                icon_type="whatsapp",
                pre_filled_message="Hi, I need help with...",
                is_enabled=True
            )
            db.add(widget_config)
            db.commit()
            db.refresh(widget_config)

        return widget_config

    def update_widget_configuration(
        self,
        business_id: str,
        config_data: Dict[str, Any],
        db: Session
    ) -> WidgetConfiguration:
        """
        Update the widget configuration for a business
        """
        widget_config = db.query(WidgetConfiguration).filter(
            WidgetConfiguration.business_id == business_id
        ).first()

        # If no configuration exists, create a new one
        if not widget_config:
            widget_config = WidgetConfiguration(
                business_id=business_id,
                **config_data
            )
            db.add(widget_config)
        else:
            # Update existing configuration
            for key, value in config_data.items():
                if hasattr(widget_config, key):
                    setattr(widget_config, key, value)

        db.commit()
        db.refresh(widget_config)

        return widget_config

    def generate_widget_code(
        self,
        business_id: str,
        db: Session
    ) -> Dict[str, str]:
        """
        Generate the HTML/JS code for the WhatsApp widget
        """
        config = self.get_widget_configuration(business_id, db)

        if not config.is_enabled:
            return {
                "html_code": "",
                "js_code": "",
                "status": "disabled"
            }

        # Generate HTML code for the widget
        html_code = f'''
<div id="whatsapp-widget-container" style="position: fixed; {config.position.split('-')[1]}: 20px; {config.position.split('-')[0]}: 20px; z-index: 9999;">
  <a href="https://wa.me/PHONE_NUMBER?text={config.pre_filled_message}" target="_blank">
    <div style="background-color: {config.color_scheme}; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="30" height="30">
        <path fill="white" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.297-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.158 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.686 1.448h.002c6.554 0 11.89-5.335 11.892-11.893A11.821 11.821 0 0020.465 3.385"/>
      </svg>
    </div>
  </a>
</div>
'''

        # Generate JavaScript code for the widget
        js_code = f'''
<script>
  // WhatsApp Widget Configuration
  const widgetConfig = {{
    position: '{config.position}',
    colorScheme: '{config.color_scheme}',
    iconType: '{config.icon_type}',
    preFilledMessage: '{config.pre_filled_message}',
    isEnabled: {str(config.is_enabled).lower()}
  }};

  // Additional functionality can be added here
  console.log('WhatsApp Widget loaded with config:', widgetConfig);
</script>
'''

        return {
            "html_code": html_code.strip(),
            "js_code": js_code.strip(),
            "status": "generated"
        }


# Global instance
widget_service = WidgetService()