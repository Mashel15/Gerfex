class InternalIntelligenceProvider:

    def provider_name(self):
        raise NotImplementedError

    def provider_status(self):
        raise NotImplementedError

    def think(self, prompt, context=None):
        raise NotImplementedError

    def learn(self, lesson):
        raise NotImplementedError

    def propose_learning(self, lesson):
        raise NotImplementedError

    def get_pending_lessons(self):
        raise NotImplementedError

    def get_approved_knowledge(self):
        raise NotImplementedError

    def get_learned_skills(self):
        raise NotImplementedError
