configuration=
{
	daemon=false,
	pathSeparator="/",

	logAppenders=
	{
		{
			name="console appender",
			type="coloredConsole",
			level=6
		}
	},
	
	applications=
	{
		rootDirectory="/usr/lib/crtmpserver/applications",
		{
			description="FLV Playback Sample",
			name="flvplayback",
			protocol="dynamiclinklibrary",
			default=true,
			aliases=
			{
				"simpleLive",
				"vod",
				"live",
				"WeeklyQuest",
				"SOSample",
				"oflaDemo",
			},
			acceptors = 
			{
                {
					ip="0.0.0.0",
					port=1936,
					protocol="inboundRtmp",
                    localStreamName="tcpchan4"
				},
				{
					ip="127.0.0.1",
					port=47768,
					--protocol="inboundTcpTs",--
					protocol="inboundLiveFlv",
                    localStreamName="tcpchan5"
				},
			},
			validateHandshake=false,
			--keyframeSeek=true,
			keyframeSeek=false,
			seekGranularity=1.5, --in seconds, between 0.1 and 600
			clientSideBuffer=12, --in seconds, between 5 and 30
			--generateMetaFiles=true, --this will generate seek/meta files on application startup
			--renameBadFiles=false,
			mediaFolder="./media",
		},
	}
}
