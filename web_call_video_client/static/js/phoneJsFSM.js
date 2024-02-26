/* Copyright (C) 2018 Freetech Solutions

 This file is part of OMniLeads

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see http://www.gnu.org/licenses/.

*/

var PhoneFSM = new StateMachine.factory({
    init: 'Inactive',
    transitions: [
        // Inactive
      { name: 'startCallProcess',       from: 'Inactive',       to: 'Connecting' },
        // Connecting
      { name: 'disconnected',           from: 'Connecting',     to: 'Inactive' },
      { name: 'failedRegistration',     from: 'Connecting',     to: 'Inactive' },
      { name: 'call',                   from: 'Connecting',     to: 'Calling' },
        // Calling
      { name: 'endCall',                from: 'Calling',        to: 'Inactive' },
      { name: 'connectCall',            from: 'Calling',        to: 'OnCall' },
        // OnCall
      { name: 'endCall',                from: 'OnCall',         to: 'Inactive' },
    ],

});
