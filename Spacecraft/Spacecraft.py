# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 10:52:34 2020

@author: EO
"""
import numpy as np
from .SubSystems import SubSystems
from Dynamics.Dynamics import Dynamics
from Dynamics.ClockGenerator import ClockGenerator


class Spacecraft(SubSystems):
    def __init__(self, spacecraft_properties, components_properties, simtime):

        self.simtime = simtime
        self.dynamics = Dynamics(spacecraft_properties, self.simtime)

        self.master_data_satellite = {}
        print('Spacecraft name: ' + str(spacecraft_properties['Attitude']['spacecraft_name']))
        self.spacecraft_model = spacecraft_properties['Attitude']['spacecraft_model']
        # Add components
        print('Spacecraft components:')
        SubSystems.__init__(self, components_properties, self.dynamics, self.simtime.stepsimTime)
        self.clockgenerator = ClockGenerator(self.subsystems, self.system_name)
        self.ext_report = {}

    def update(self):
        # Dynamics updates
        self.dynamics.update()

        # Tick the time on component
        k = 0
        for i_ in range(int(self.simtime.stepsimTime*1000)):
            self.clockgenerator.tick_to_components()
            k += 1
        return

    def update_data(self):
        # Historical data
        self.save_log_values()
        self.dynamics.attitude.save_attitude_data()
        self.dynamics.trajectory.save_orbit_data()
        self.dynamics.ephemeris.save_ephemeris_data()
        self.simtime.save_simtime_data()

    def add_report(self, ext_report):
        self.ext_report = {**self.ext_report, **ext_report}

    def create_report(self):
        report_attitude = self.dynamics.attitude.get_log_values()
        report_orbit = self.dynamics.trajectory.get_log_values()
        report_ephemerides = self.dynamics.ephemeris.selected_center_object.get_log_values()
        report_timelog = self.simtime.get_log_values()

        report_sensor = {}
        report_subsystems = {}
        i = 1
        for subsys in self.system_name:
            if self.subsystems[subsys] is not None:
                report_subsystems = {**report_subsystems, **self.subsystems[subsys].get_log_values()}
                if hasattr(self.subsystems[subsys].components, 'gyro'):
                    gyro = self.subsystems[subsys].components.gyro
                    report_sensor['gyro_omega' + str(i) + '_c(X)[rad/s]'] = np.array(gyro.historical_omega_c)[:, 0]
                    report_sensor['gyro_omega' + str(i) + '_c(Y)[rad/s]'] = np.array(gyro.historical_omega_c)[:, 1]
                    report_sensor['gyro_omega' + str(i) + '_c(Z)[rad/s]'] = np.array(gyro.historical_omega_c)[:, 2]
                    i += 1
                if hasattr(self.subsystems[subsys].components, 'thruster'):
                    ti = 1
                    for thr in self.subsystems[subsys].components.thruster:
                        report_sensor['Mag_Thrust_' + str(ti) + ' [N]'] = np.array(thr.historical_mag_thrust)
                        ti += 1

        self.master_data_satellite = {**report_timelog,
                                      **report_attitude,
                                      **report_orbit,
                                      **report_sensor,
                                      **report_ephemerides,
                                      **report_subsystems,
                                      **self.ext_report}
