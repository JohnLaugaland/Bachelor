import simpy
import random
import pprint


class GlobalVariable():

    simulation_time = 360
    num_nodes = 50
    speed_in_system = 0.125
    adv_frame_time = 0.001040                  #0.001040
    adv_interval = 1
    offset_delay = 0.003172                    #0.003172
    radio_delay = 0.000002
    ext_adv_frame_time = 0.004112              #0.004112
    observer_current_frequency = 37
    fail_teller = 0
    sent_teller = 0
    sent_ADV_teller = 0
    sent_EXT_ADV_teller = 0

    adv_success_teller = 0
    adv_collisjon_teller = 0
    ext_adv_collisjon_teller = 0
    adv_wrong_freq_teller = 0
    adv_change_freq_teller = 0
    ext_adv_half_success = 0
    ext_adv_full_success = 0

class Package(object):
    def __init__(self, node_name, package_name, package_frequency):
        self.which_node = node_name
        self.package_name = package_name
        self.pakke_frekvens = package_frequency

        self.fail_to_mutch_obs = False
        self.collision = False
        self.change_frequency = False

        self.start_tid = 0
        self.stop_tid = 0

        self.next_package = 0

def send(node_name, package_name, package_freqency, frame_time, type_package, next_packege):

    p_freq = package_freqency
    pakke_id = (node_name, package_name)
    p_start_time = env.now
    p_adv_stop_time = p_start_time + frame_time

    frame = Package(node_name, package_name, p_freq)
    frame.start_tid = p_start_time
    frame.stop_tid = p_adv_stop_time
    frame.next_package = next_packege

    if type_package== True:
        Data_Base.puts_packs_in_air(Data_Base, frame, pakke_id)
    elif type_package == False:
        Data_Base.add_ext_frame_in_transmit(Data_Base, frame, pakke_id)

    if p_freq != GlobalVariable.observer_current_frequency:
        frame.fail_to_mutch_obs = True

    check_collision(frame, pakke_id, type_package)

    yield env.timeout(frame_time)

    if type_package == True:
        if p_freq != GlobalVariable.observer_current_frequency and frame.fail_to_mutch_obs != True:
            frame.change_frequency = True
            GlobalVariable.adv_change_freq_teller += 1
        if frame.collision == True:
            GlobalVariable.adv_collisjon_teller += 1
        if(frame.collision == False) and (frame.fail_to_mutch_obs == False) and (frame.change_frequency == False):
            GlobalVariable.adv_success_teller += 1
            yield env.timeout(GlobalVariable.radio_delay)
            GlobalVariable.observer_current_frequency = next_packege

            yield env.timeout(GlobalVariable.offset_delay + GlobalVariable.ext_adv_frame_time + GlobalVariable.radio_delay) #
            GlobalVariable.ext_adv_half_success += 1
            GlobalVariable.observer_current_frequency = 37

    if type_package == False:
        if p_freq != GlobalVariable.observer_current_frequency:
            frame.fail_to_mutch_obs = True
        elif p_freq != GlobalVariable.observer_current_frequency and frame.fail_to_mutch_obs != True:
            frame.change_frequency = True
            GlobalVariable.adv_change_freq_teller += 1
        if frame.collision == True:
            GlobalVariable.ext_adv_collisjon_teller += 1
        elif frame.collision == False and frame.fail_to_mutch_obs == False:
            GlobalVariable.ext_adv_full_success += 1

    if(type_package==True):
        Data_Base.slet_adv_frame_fra_transmit(0, pakke_id)
    elif(type_package == False):
        Data_Base.slet_ext_frame_fra_transmit(0, pakke_id)


def node_funk(env, node_name):

    times_sent = 0
    times_sent_adv = 0
    times_sent_ext_adv = 0
    adv_package_frequency = 37
    ext_package_frequency = random.randint(0, 37)
    start_delay = random.uniform(0, 1)
    yield env.timeout(start_delay)

    while True:
        type_package = True
        adv_delay = random.uniform(0, 0.01)
        package_name = (('Frame %d') % times_sent_adv)
        env.process(send(node_name, package_name, adv_package_frequency, GlobalVariable.adv_frame_time, type_package, ext_package_frequency))
        times_sent += 1
        times_sent_adv += 1
        GlobalVariable.sent_teller += 1
        GlobalVariable.sent_ADV_teller += 1

        yield env.timeout(GlobalVariable.adv_frame_time + GlobalVariable.offset_delay ) # + GlobalVariable.offset_delay

        type_package = False
        ext_pakke_navn = (('ExtFrame %d') % times_sent_ext_adv)
        env.process(send(node_name, ext_pakke_navn, ext_package_frequency, GlobalVariable.ext_adv_frame_time, type_package, adv_package_frequency))
        times_sent += 1
        times_sent_ext_adv += 1
        GlobalVariable.sent_teller += 1
        GlobalVariable.sent_EXT_ADV_teller += 1
        ext_package_frequency = random.randint(0, 37)
        end_delay = GlobalVariable.adv_interval + adv_delay - GlobalVariable.adv_frame_time - GlobalVariable.offset_delay - GlobalVariable.ext_adv_frame_time
        yield env.timeout(end_delay)


def check_collision(frame, pakke_id, type_pakke):
    if type_pakke == True:
        for key in Data_Base.frames_in_transmit.keys():
            if key != pakke_id:
                if Data_Base.frames_in_transmit[key].pakke_frekvens == frame.pakke_frekvens:
                    if (Data_Base.frames_in_transmit[key].stop_tid > frame.start_tid) and (Data_Base.frames_in_transmit[key].start_tid < frame.stop_tid):
                        frame.collision = True
                        Data_Base.frames_in_transmit[key].collision = True
                        Data_Base.all_frames_in_transmit[key].collision = True
    else:
        for key in Data_Base.ext_frames_in_transmit.keys():
            if key != pakke_id:
                if Data_Base.ext_frames_in_transmit[key].pakke_frekvens == frame.pakke_frekvens:   #ext_pakke_frequency til pakke_frekvens
                    if (Data_Base.ext_frames_in_transmit[key].stop_tid > frame.start_tid) and (Data_Base.ext_frames_in_transmit[key].start_tid < frame.stop_tid):
                        frame.collision = True
                        Data_Base.ext_frames_in_transmit[key].collision = True
                        Data_Base.all_ext_frames_in_transmit[key].collision = True

class Data_Base(object):

    frames_in_transmit = {}
    ext_frames_in_transmit = {}

    all_frames_in_transmit = {}
    all_ext_frames_in_transmit = {}

    def puts_packs_in_air(self, frame, pakke_id):
        Data_Base.frames_in_transmit[pakke_id] = frame
        Data_Base.all_frames_in_transmit[pakke_id] = frame

    def add_ext_frame_in_transmit(self, frame, pakke_id):
        Data_Base.ext_frames_in_transmit[pakke_id] = frame
        Data_Base.all_ext_frames_in_transmit[pakke_id] = frame

    def slet_adv_frame_fra_transmit(self, pakke_id):
        del Data_Base.frames_in_transmit[pakke_id]
        return

    def slet_ext_frame_fra_transmit(self, pakke_id):
        del Data_Base.ext_frames_in_transmit[pakke_id]
        return

def setup(env):
    n_t = GlobalVariable.num_nodes
    try:
        for i in range(n_t):
            env.process(node_funk(env, 'Node %d' % i))
            print("Process (node): %d is laid and runs in parallel with other " %i)
    except: #will never occur
        print("Cant add Nodes to virtual enviermant")
        yield

if __name__ == "__main__":
    env = simpy.Environment()
    env.process(setup(env))
    env.run(until=GlobalVariable.simulation_time)



def test_funk_for_collision_teller():

    test_adv_collision = 0
    test_adv_not_collision = 0
    test_adv_mutch_obs = 0
    test_adv_not_mutch_obs = 0
    adv_full_success = 0

    for key in Data_Base.all_frames_in_transmit.keys():
        if Data_Base.all_frames_in_transmit[key].collision == True:
            test_adv_collision += 1
        elif Data_Base.all_frames_in_transmit[key].collision == False:
            test_adv_not_collision += 1
        if Data_Base.all_frames_in_transmit[key].fail_to_mutch_obs == True:
            test_adv_not_mutch_obs += 1
        if Data_Base.all_frames_in_transmit[key].fail_to_mutch_obs == False:
            test_adv_mutch_obs += 1
        if(Data_Base.all_frames_in_transmit[key].fail_to_mutch_obs == False) and (Data_Base.all_frames_in_transmit[key].collision == False):
            adv_full_success += 1

    #percentage calculation
    prosent_collisjon_ADV = test_adv_collision/GlobalVariable.sent_ADV_teller
    prosent_success_ADV = adv_full_success / GlobalVariable.sent_ADV_teller

    print("[1.1]Check funk for ADV shows how many packages in Collision: %d and the percentage is (%4f)" %(test_adv_collision, prosent_collisjon_ADV))
    print("[1.2]Check funk for ADV shows how many packages are NOT in Collision: %d" % test_adv_not_collision)
    print("[1.3]Check funk for ADV shows how many ADV packages match witch OBS: %d" % test_adv_mutch_obs)
    print("[1.4]Check funk for ADV half success: %d and the percentage is (%4f)" % (adv_full_success, prosent_success_ADV))

def test_funk_for_ext_collision_teller():
    test_ext_collision = 0
    test_ext_not_collision = 0
    test_ext_mutch_obs = 0
    test_ext_not_mutch_obs = 0
    full_success=0
    for key in Data_Base.all_ext_frames_in_transmit.keys():
        if Data_Base.all_ext_frames_in_transmit[key].collision == True:
            test_ext_collision += 1
        elif Data_Base.all_ext_frames_in_transmit[key].collision == False: # or (Data_Base.ext_frames_in_transmit[key].fail_to_mutch_obs == False):
            test_ext_not_collision += 1
        #tests mutch or not mutch with OBS
        if Data_Base.all_ext_frames_in_transmit[key].fail_to_mutch_obs == False: #den er feil fordi i utgangspunkt parameteren er satt på False fra statren
            test_ext_mutch_obs += 1
        elif Data_Base.all_ext_frames_in_transmit[key].fail_to_mutch_obs == True:
            test_ext_not_mutch_obs += 1
        #tests for full suksess
        if (Data_Base.all_ext_frames_in_transmit[key].fail_to_mutch_obs == False) and (Data_Base.all_ext_frames_in_transmit[key].collision == False):
            full_success += 1

    #prosent counter
    prosent_collisjon_EXT_ADV = test_ext_collision / GlobalVariable.sent_ADV_teller
    prosent_success_EXT = full_success / GlobalVariable.sent_EXT_ADV_teller

    print("[2.1]Check funk for EXT_ADV shows how many packages in Collision: %d and the percentage is (%4f)" %(test_ext_collision, prosent_collisjon_EXT_ADV))
    print("[2.2]Check funk for EXT_ADV shows how many packages are NOT in Collision: %d" % test_ext_not_collision)
    print("[2.3]Check funk for EXT_ADV shows how many packages NOT Matches with OBS: %d" %test_ext_not_mutch_obs)
    print("[2.4]Check funk for EXT_ADV shows how many FULL SUCCESS: %d and percent are (%4f Percent)" %(full_success, prosent_success_EXT))

check_1 = test_funk_for_collision_teller()
check_2 = test_funk_for_ext_collision_teller()

print("[node info] adv_success_teller: %d" %GlobalVariable.adv_success_teller)
#print("[node info] ext_adv_halv_suksess: %d" % GlobalVariable.ext_adv_half_success)
print("[node info] sent_ALT_teller: %d" % (GlobalVariable.sent_teller))
print("[node info] sent_ADV_teller: %d" % (GlobalVariable.sent_ADV_teller))
print("[node info] sent_EXT_ADV_teller: %d" % (GlobalVariable.sent_EXT_ADV_teller))
print("[node info] ext_adv_full success: %d" % GlobalVariable.ext_adv_full_success)
pprint.pprint(vars(Data_Base.all_ext_frames_in_transmit["Node 0", "ExtFrame 0"]))























