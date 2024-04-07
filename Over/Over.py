import hassapi as hass
import requests as req
#
# App to send notification about shelly overheating, overpowering, overvoltage
# Args:
#
# Release Notes
#
# Version 1.0:
#   Initial Version
class Over(hass.Hass):
    def initialize(self):
        for sensor in self.args["over_sensors"]:
            self.listen_state(self.state_change, sensor)
            #self.listen_state(self.state_change, sensor, new="on", duration=int(self.args["numero_secondi_off"]))

    def state_change(self, entity, attribute, old, new, kwargs):
        if new != "":
            stato = self.get_state(entity)
            message = "{} changed to {}".format(self.friendly_name(entity), new)
            self.log(message)
            self.invia_notifiche(message)
    
    ## invio notifiche a tutti i dispositivi previsti nel file di configurazione
    def invia_notifiche(self, messaggio):
        for servizio_notifica in self.args["notification_services"]:
            service = "notify/" + servizio_notifica
            self.call_service(service, title = "Konnected:", message = messaggio)
        return