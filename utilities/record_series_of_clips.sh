echo Starting HerpCam Clip Recording
echo Press Q to exit.

trap 'kill $(jobs -p)' SIGINT SIGTERM EXIT
# trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

while true; do
    printf "Next clip\n"
    current_time=$(date "+%Y.%m.%d-%H.%M.%S")
    # file_name=bushmasters
    file_name=/home/ian/mang_vipers/$current_time.mp4
    ffmpeg -i rtsp://admin:b22shm**stters@10.10.32.206:554/Streaming/Channels/102 -acodec copy -vcodec copy $file_name -nostdin  &
    vlc_pid=$!

    sleep 30m
    kill $vlc_pid
    read -t 0.25 -N 1 input
    if [[ $input = "q" ]] || [[ $input = "Q" ]]; then
        echo
        break 
    fi
done
