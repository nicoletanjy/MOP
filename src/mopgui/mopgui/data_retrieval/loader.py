__author__ = "David Rusk <drusk@uvic.ca>"

import threading


class AsynchronousImageLoader(object):
    """
    Loads images asynchronously from the rest of the application.
    """

    def __init__(self, resolver, image_retriever):
        self.resolver = resolver
        self.image_retriever = image_retriever

    def start_loading(self, astrom_data,
                      image_loaded_callback=None,
                      all_loaded_callback=None):

        self.image_loaded_callback = image_loaded_callback
        self.all_loaded_callback = all_loaded_callback

        lookupinfo = []
        for source in astrom_data.sources:
            for reading in source:
                image_uri = self.resolver.resolve_uri(reading.obs)
                lookupinfo.append((image_uri, reading))

        self.do_loading(lookupinfo)

    def do_loading(self, lookupinfo):
        SerialImageRetrievalThread(self, self.image_retriever,
                                   lookupinfo).start()

    def on_image_loaded(self, image, converter, reading):
        reading.image = image
        reading.converter = converter

        if self.image_loaded_callback is not None:
            self.image_loaded_callback()

    def on_all_loaded(self):
        if self.all_loaded_callback is not None:
            self.all_loaded_callback()


class SerialImageRetrievalThread(threading.Thread):
    """
    Retrieve each image serially, but in this separate thread so it can
    happen in the background.
    """

    def __init__(self, loader, image_retriever, lookupinfo):
        super(SerialImageRetrievalThread, self).__init__()

        self.loader = loader
        self.image_retriever = image_retriever
        self.lookupinfo = lookupinfo

    def run(self):
        for image_uri, reading in self.lookupinfo:
            image, converter = self.image_retriever.retrieve_image(image_uri, reading)
            self.loader.on_image_loaded(image, converter, reading)

        self.loader.on_all_loaded()
