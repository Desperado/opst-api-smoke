import json
import random
import time
import sys
import traceback

import requests
from colorama import Fore


KEYSTONE_URL = 'http://172.16.0.2:5000/v3'
NEUTRON_URL = 'http://172.16.0.2:9696/v2.0'
NOVA_URL = 'http://172.16.0.2:8774/v2'
CINDER_URL = 'http://172.16.0.2:8776/v1'
GLANCE_URL = 'http://172.16.0.2:9292/v2'

ADMIN_USER = 'admin'
ADMIN_PASSWORD = 'admin'
ADMIN_TOKEN = 'ADMIN'

EXTERNAL_NETWORK_ID = 'd7046b2f-ae89-4647-ba51-21e91ab9a608'
IMAGE_ID = 'a940fddd-6551-48a6-8f10-e88a3f3092a6'
FLAVOR_ID = 'd39c3862-bd53-4683-a80b-7a5c4dc24eae'

HEADERS = {'Accept': 'application/json', 'Content-type': 'application/json'}

suffix = repr(random.random())[2:]

DOMAIN = 'domain_{}'.format(suffix)
PROJECT = 'project_{}'.format(suffix)
USER = 'user_{}'.format(suffix)
NETWORK = 'network_{}'.format(suffix)
ROUTER = 'router_{}'.format(suffix)
KEYPAIR = 'keypair_{}'.format(suffix)
INSTANCE = 'instance_{}'.format(suffix)
INSTANCE_SNAPSHOT = 'instance_snap_{}'.format(suffix)
VOLUME = 'volume_{}'.format(suffix)
VOLUME_SNAPSHOT = 'volume_snap_{}'.format(suffix)


def sleep(seconds):
    print 'Sleeping for {} seconds'.format(seconds)
    for i in range(seconds):
        time.sleep(1)
        sys.stdout.write('.')
        sys.stdout.flush()
    sys.stdout.write('\n\n')


def service_request(service_endpoint, method, path, headers, body=None):
    method_name = traceback.extract_stack(limit=2)[-2][2]
    action = method_name.replace('_', ' ').upper()
    print(Fore.YELLOW + '##### {} #####'.format(action) + Fore.RESET)
    print '=== R E Q U E S T ===\n' \
          'METHOD:  {}\n' \
          'URL:     {}\n' \
          'HEADERS: {}'.format(method.upper(), service_endpoint + path, headers)
    if body:
        print 'BODY:    {}'.format(body) if body else None

    if body:
        resp = getattr(requests, method)('{}/{}'.format(service_endpoint, path), json.dumps(body), headers=headers)
    else:
        resp = getattr(requests, method)('{}/{}'.format(service_endpoint, path), headers=headers)

    response_log = '=== R E S P O N S E ===\n' \
                   'CODE:    {}\n' \
                   'HEADERS: {}\n' \
                   'BODY:    {}\n'.format(resp.status_code, dict(resp.headers), resp.text)
    if resp.status_code > 300:
        print(Fore.RED + response_log + Fore.RESET)
    else:
        print(Fore.GREEN + response_log + Fore.RESET)

    try:
        resp_body = resp.json()
    except ValueError:
        resp_body = resp.text

    return {'headers': resp.headers, 'body': resp_body}


def auth_headers(token):
    headers = HEADERS
    headers['X-Auth-Token'] = token
    return headers


# KEYSTONE

def get_services(token):
    return service_request(KEYSTONE_URL, 'get', '/services', auth_headers(token))


def get_endpoints(token):
    return service_request(KEYSTONE_URL, 'get', '/endpoints', auth_headers(token))


def get_domains(token):
    return service_request(KEYSTONE_URL, 'get', '/domains', auth_headers(token))


def create_domain(token, name):
    body = \
        {
            'domain': {
                'name': name
            }
        }
    return service_request(KEYSTONE_URL, 'post', '/domains', auth_headers(token), body)


def disable_domain(token, domain_id):
    body = \
        {
            'domain': {
                'enabled': False
            }
        }
    return service_request(KEYSTONE_URL, 'patch', '/domains/{}'.format(domain_id), auth_headers(token), body)


def delete_domain(token, domain_id):
    return service_request(KEYSTONE_URL, 'delete', '/domains/{}'.format(domain_id), auth_headers(token))


def create_project(token, name, domain_id):
    body = \
        {
            'project': {
                'name': name,
                'domain_id': domain_id,
                'enabled': True
            }
        }
    return service_request(KEYSTONE_URL, 'post', '/projects', auth_headers(token), body)


def delete_project(token, project_id):
    return service_request(KEYSTONE_URL, 'delete', '/projects/{}'.format(project_id), auth_headers(token))


def get_projects(token):
    return service_request(KEYSTONE_URL, 'get', '/projects', auth_headers(token))


def create_user(token, username, password, domain_id, project):
    body = \
        {
            'user': {
                'name': username,
                'password': password,
                'domain_id': domain_id,
                'default_project': project
            }
        }
    return service_request(KEYSTONE_URL, 'post', '/users', auth_headers(token), body)


def delete_user(token, user_id):
    return service_request(KEYSTONE_URL, 'delete', '/users/{}'.format(user_id), auth_headers(token))


def get_users(token):
    return service_request(KEYSTONE_URL, 'get', '/users', auth_headers(token))


def get_user_roles(token, user_id):
    return service_request(KEYSTONE_URL, 'get', '/users/{}/roles'.format(user_id), auth_headers(token))


def get_user_roles_in_project(token, project_id, user_id):
    return service_request(KEYSTONE_URL, 'get', '/projects/{}/users/{}/roles'.format(project_id, user_id),
                           auth_headers(token))


def grant_user_role_in_project(token, project_id, user_id, role_id):
    return service_request(KEYSTONE_URL, 'put', '/projects/{}/users/{}/roles/{}'.format(project_id, user_id, role_id),
                           auth_headers(token))


def get_roles(token):
    return service_request(KEYSTONE_URL, 'get', '/roles', auth_headers(token))


def get_token(username, password, domain, project):
    body = \
        {
            'auth': {
                'identity': {
                    'methods': [
                        'password'
                    ],
                    'password': {
                        'user': {
                            'domain': {
                                'name': domain
                            },
                            'name': username,
                            'password': password
                        }
                    }
                },
                'scope': {
                    'project': {
                        'domain': {
                            'name': domain
                        },
                        'name': project
                    }
                }
            }
        }
    return service_request(KEYSTONE_URL, 'post', '/auth/tokens', HEADERS, body)


# NEUTRON

def create_network(token, name):
    body = \
        {
            'network': {
                'name': name
            }
        }
    return service_request(NEUTRON_URL, 'post', '/networks', auth_headers(token), body)


def delete_network(token, network_id):
    return service_request(NEUTRON_URL, 'delete', '/networks/{}'.format(network_id), auth_headers(token))

def get_networks(token):
    return service_request(NEUTRON_URL, 'get', '/networks', auth_headers(token))

def create_subnet(token, network_id):
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(3))))
    cidr = '{}.0/24'.format(ip)
    body = \
        {
            'subnet': {
                'ip_version': 4,
                'cidr': cidr,
                'network_id': network_id
            }
        }
    return service_request(NEUTRON_URL, 'post', '/subnets', auth_headers(token), body)


def delete_subnet(token, subnet_id):
    return service_request(NEUTRON_URL, 'delete', '/subnets/{}'.format(subnet_id), auth_headers(token))


def create_router(token, name, network_id):
    body = \
        {
            'router': {
                'name': name,
                'external_gateway_info': {
                    'network_id': network_id
                }
            }
        }
    return service_request(NEUTRON_URL, 'post', '/routers', auth_headers(token), body)


def delete_router(token, router_id):
    return service_request(NEUTRON_URL, 'delete', '/routers/{}'.format(router_id), auth_headers(token))


def add_router_interface(token, router_id, subnet_id):
    body = \
        {
            'subnet_id': subnet_id
        }
    return service_request(NEUTRON_URL, 'put', '/routers/{}/add_router_interface'.format(router_id),
                           auth_headers(token), body)


def delete_router_interface(token, router_id, subnet_id):
    body = \
        {
            'subnet_id': subnet_id
        }
    return service_request(NEUTRON_URL, 'put', '/routers/{}/remove_router_interface'.format(router_id),
                           auth_headers(token), body)

def get_ports(token):
    return service_request(NEUTRON_URL, 'get', '/ports',
                           auth_headers(token))

def associate_floating_ip(token, network_id, port_id):
    body = \
        {
        "floatingip":{
        "floating_network_id":network_id,
        "port_id":port_id
        }
    }
    return service_request(NEUTRON_URL, 'post', '/floatingips'.format(project_id), auth_headers(token),
                           body)

def delete_floating_ip(token, floatingip_id):
    return service_request(NEUTRON_URL, 'delete', '/floatingips/{}'.format(floatingip_id), auth_headers(token))


# NOVA

def create_keypair(token, project_id, name):
    body = \
        {
            'keypair': {
                'name': name
            }
        }
    return service_request(NOVA_URL, 'post', '/{}/os-keypairs'.format(project_id), auth_headers(token), body)


def delete_keypair(token, project_id, keypair_id):
    return service_request(NOVA_URL, 'delete', '/{}/os-keypairs/{}'.format(project_id, keypair_id), auth_headers(token))


def create_instance(token, name, project_id, flavor_id, image_id, network_id):
    body = \
        {
            'server': {
                'flavorRef': flavor_id,
                'imageRef': image_id,
                'name': name,
                'networks': [
                    {
                        'uuid': network_id
                    }
                ]
            }
        }
    return service_request(NOVA_URL, 'post', '/{}/servers'.format(project_id), auth_headers(token), body)


def delete_instance(token, project_id, instance_id):
    return service_request(NOVA_URL, 'delete', '/{}/servers/{}'.format(project_id, instance_id), auth_headers(token))


def get_instance(token, project_id, instance_id):
    return service_request(NOVA_URL, 'get', '/{}/servers/{}'.format(project_id, instance_id), auth_headers(token))


def attach_volume(token, project_id, instance_id, volume_id):
    body = \
        {
            'volumeAttachment': {
                'volumeId': volume_id,
                'device': '/dev/vdd'
                          ''
            }
        }
    return service_request(NOVA_URL, 'post', '/{}/servers/{}/os-volume_attachments'.format(project_id, instance_id),
                           auth_headers(token), body)

def get_attachments(token, project_id, instance_id):
    return service_request(NOVA_URL, 'get', '/{}/servers/{}/os-volume_attachments'.format(project_id, instance_id),
                           auth_headers(token))


def detach_volume(token, project_id, instance_id, attachment_id):
    return service_request(NOVA_URL, 'delete', '/{}/servers/{}/os-volume_attachments/{}'.format(project_id,
                            instance_id, attachment_id), auth_headers(token))


def create_instance_snapshot(token, project_id, instance_id, name):
    body = \
        {
            'createImage': {
                'name': name,
                'is_public': True,
            }
        }
    return service_request(NOVA_URL, 'post', '/{}/servers/{}/action'.format(project_id, instance_id),
                           auth_headers(token), body)


def delete_image(token, image_id):
    return service_request(NOVA_URL, 'delete', '/{}/images/{}'.format(project_id, image_id), auth_headers(token))

# CINDER

def create_volume(token, project_id, name, size):
    body = \
        {
            'volume': {
                'display_name': name,
                'size': size
            }
        }
    return service_request(CINDER_URL, 'post', '/{}/volumes'.format(project_id), auth_headers(token), body)


def delete_volume(token, project_id, volume_snapshot_id):
    return service_request(CINDER_URL, 'delete', '/{}/volumes/{}'.format(project_id, volume_snapshot_id),
                           auth_headers(token))

def get_volume_snapshot_info(token, project_id, volume_snapshot_id):
    return service_request(CINDER_URL, 'get', '/{}/snapshots/{}'.format(project_id, volume_snapshot_id),
                           auth_headers(token))

def get_volume_info(token, project_id, volume_id):
    return service_request(CINDER_URL, 'get', '/{}/volumes/{}'.format(project_id, volume_id),
                           auth_headers(token))

def get_snapshots_from_volumes(token, project_id):
    return service_request(CINDER_URL, 'get', '/{}/snapshots'.format(project_id), auth_headers(token))

def get_volumes(token, project_id):
    return service_request(CINDER_URL, 'get', '/{}/volumes'.format(project_id), auth_headers(token))


def create_volume_snapshot(token, project_id, volume_id, name):
    body = \
        {
            'snapshot': {
                'name': name,
                'volume_id': volume_id,
                'is_public': True,
            }
        }
    return service_request(CINDER_URL, 'post', '/{}/snapshots'.format(project_id), auth_headers(token),
                           body)


def delete_volume_snapshot(token, project_id, volume_id):
    return service_request(CINDER_URL, 'delete', '/{}/snapshots/{}'.format(project_id, volume_id), auth_headers(token))


# GLANCE

def get_images(token):
    return service_request(GLANCE_URL, 'get', '/images', auth_headers(token))

def get_image_info(token, image_id):
    return service_request(GLANCE_URL, 'get', '/images/{}'.format(image_id), auth_headers(token))

print \
    'DOMAIN:   {}\n' \
    'PROJECT:  {}\n' \
    'USER:     {}\n' \
    'PASSWORD: 123qwe\n' \
    'NETWORK:  {}\n' \
    'ROUTER:   {}\n' \
    'KEYPAIR:  {}\n' \
    'INSTANCE: {}\n' \
    'VOLUME:   {}\n'.format(DOMAIN, PROJECT, USER, NETWORK, ROUTER, KEYPAIR, INSTANCE, VOLUME)


# Create domain
domain_id = create_domain(ADMIN_TOKEN, DOMAIN)['body']['domain']['id']

# Create project
project_id = create_project(ADMIN_TOKEN, PROJECT, domain_id)['body']['project']['id']

# Create user
user_id = create_user(ADMIN_TOKEN, USER, '123qwe', domain_id, PROJECT)['body']['user']['id']

# Assign role to user
roles = get_roles(ADMIN_TOKEN)['body']['roles']
for role in roles:
    if role['name'] == '_member_':
        member_role_id = role['id']
grant_user_role_in_project(ADMIN_TOKEN, project_id, user_id, member_role_id)

# Get token
token = get_token(USER, '123qwe', DOMAIN, PROJECT)['headers']['x-subject-token']

# Create network
network_id = create_network(token, NETWORK)['body']['network']['id']

# Create subnet
subnet_id = create_subnet(token, network_id)['body']['subnet']['id']

# Create router
router_id = create_router(token, ROUTER, EXTERNAL_NETWORK_ID)['body']['router']['id']

# Add router interface for internal network
interface_id = add_router_interface(token, router_id, subnet_id)['body']['id']

# Create keypair
keypair_name = create_keypair(token, project_id, KEYPAIR)['body']['keypair']['name']

# Create volume
volume_id = create_volume(token, project_id, VOLUME, 1)['body']['volume']['id']

# Wait for the volume to build
print 'Waiting for the volume to finish building'
sleep(10)

# Create volume snapshot
volume_snapshot_id = create_volume_snapshot(token, project_id, volume_id, VOLUME_SNAPSHOT)['body']['snapshot']['id']

# Create instance
instance_id = create_instance(token, INSTANCE, project_id, FLAVOR_ID, IMAGE_ID, network_id)['body']['server']['id']

# Wait for the instance to build
print 'Waiting for the instance to finish building'
sleep(10)

# Show instance details
get_instance(token, project_id, instance_id)

# Get network interface ports
ports = get_ports(token)


# Get instance port id
instance_port_id = ports['body']['ports'][2]['id']

# Associate floating ip
floating_ip = associate_floating_ip(token, EXTERNAL_NETWORK_ID, instance_port_id)['body']['floatingip']

floating_ip_address = floating_ip['floating_ip_address']

floating_ip_id = floating_ip['id']

delete_floating_ip(token, floating_ip_id)

# Attach volume to instance
attachment_id = attach_volume(token, project_id, instance_id, volume_id)['body']['volumeAttachment']['id']
print 'Waiting for the volume to be attached'
sleep(5)

get_attachments(token, project_id, instance_id)

detach_volume(token, project_id, instance_id, attachment_id)

# Create instance snapshot
instance_snapshot_id = \
    create_instance_snapshot(token, project_id, instance_id, INSTANCE_SNAPSHOT)['headers']['location'].split('/')[-1]

# Wait for the snapshot to build
print 'Waiting for the snapshot to finish building'
sleep(10)

print(Fore.BLUE + '-----------------------\n' \
                  '----- CLEANING UP -----\n' \
                  '-----------------------\n' + \
    Fore.RESET)

# Get Images(including snapshots)

get_images(token)

get_volume_info(token, project_id, volume_id)

get_image_info(token, instance_snapshot_id)

get_volume_snapshot_info(token, project_id, volume_snapshot_id)

# Get volumes
get_volumes(token, project_id)

# Get snapshots from volumes
get_snapshots_from_volumes(token, project_id)

delete_volume_snapshot(token, project_id, volume_snapshot_id)
print 'Waiting for the snapshot to disappear'
sleep(10)
delete_volume(token, project_id, volume_id)  # add 'volume_clear=none' to cinder.conf
delete_image(token, instance_snapshot_id)
delete_instance(token, project_id, instance_id)
print 'Waiting for the instance to disappear'
sleep(10)
delete_router_interface(token, router_id, subnet_id)
delete_router(token, router_id)
delete_subnet(token, subnet_id)
delete_network(token, network_id)
delete_user(ADMIN_TOKEN, user_id)
delete_project(ADMIN_TOKEN, project_id)
disable_domain(ADMIN_TOKEN, domain_id)
delete_domain(ADMIN_TOKEN, domain_id)
